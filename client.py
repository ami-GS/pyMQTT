import frame as fm
import socket
from settings import TYPE
from threading import Thread, Timer
import time

# TODO: multi message sender should be implemented (now single)

class Client():
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.cleanSession = 0
        self.pingThread = None
        self.connection = False
        self.messages = {}
        self.keepAlive = 2

    def send(self, frame):
        self.sock.send(frame)

    def recv(self, size = 1024):
        data = self.sock.recv(size)
        fm.parseFrame(data, self)

    def connect(self, name = "", passwd = "", will = 0, willTopic = "", willMessage = "", clean = 0, cliID = "", keepAlive = 2):
        # TODO: above default value should be considered
        self.cleanSession = clean
        self.sock.connect((self.host, self.port))
        self.connection = True
        self.keepAlive = keepAlive
        frame = fm.makeFrame(TYPE.CONNECT, 0, 0, 0, name = name, passwd = passwd,
                             will = will, willTopic = willTopic, willMessage = willMessage,
                             clean = clean, cliID = cliID, keepAlive = keepAlive)
        self.sock.send(frame)
        self.recv() #connack
        self.pingThread = Thread(target=self.__pingreq)
        self.pingThread.start()

    def disconnect(self):
        frame = fm.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.sock.send(frame)
        self.connection = False
        print "disconnect"

    def publish(self, topic, message, dup = 0, qos = 0, retain = 0, messageID = 1):
        if (qos == 1 or qos == 2) and messageID == 0:
            #error, here
            pass
        elif qos == 1:
            # save the message until puback will come
            self.messages[messageID] = [topic, message]
            # recv puback
            # remove the message
        frame = fm.makeFrame(TYPE.PUBLISH, dup, qos, retain, topic = topic, message = message, messageID = messageID)
        self.send(frame)
        self.recv() # when QoS == 0 then none return. 1 then PUBACK, 2 then PUBREC

    def pubrec(self, messageID):
        frame = fm.makeFrame(TYPE.PUBREC, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def pubrel(self, messageID):
        frame = fm.makeFrame(TYPE.PUBREL, 0, 1, 0, messageID = messageID)
        self.send(frame)

    def pubcomp(self, messageID):
        frame = fm.makeFrame(TYPE.PUBCOMP, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def initTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive, self.disconnect)

    def __pingreq(self):
        self.timer = Timer(self.keepAlive, self.disconnect)
        while self.connection:
            # Q: continuously send req? or send after receiving resp?
            time.sleep(self.keepAlive)
            self.send(fm.makeFrame(TYPE.PINGREQ, 0,0,0))
            self.timer.start()
            self.recv()

    def pubcomp(self, messgeID = 1):
        frame = fm.makeFrame(TYPE.PUBCOMP, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def subscribe(self, topics, dup = 0, qos = 0, messageID = 1):
        # topics should be [[topic1, qos1], [topic2, qos2] ...]
        if qos != 1 and len(topics) >= 2:
            print("warning: QoS should be 1 if there are several topics")
            qos = 1 # is this nice?
            # error, when qos == 1, then len(topics) is allowed to be more than or equal to 2
        frame = fm.makeFrame(TYPE.SUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)
        self.recv()

    def unsubscribe(self, topics, dup = 0, qos = 0, messageID = 1):
        # topics should be [topic1, topic2 ...]
        if qos != 1 and len(topics) >= 2:
            print("warning: QoS should be 1 if there are several topics")
            qos = 1
        frame = fm.makeFrame(TYPE.UNSUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)
        self.recv()
