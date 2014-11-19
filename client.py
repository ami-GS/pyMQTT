import frame as fm
import socket
from settings import TYPE
from threading import Thread, Timer
import time
from frame import Frame

# TODO: multi message sender should be implemented (now single)

class Client(Frame):
    def __init__(self, host, port):
        super(Client, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (host, port)
        self.cleanSession = 0
        self.pingThread = None
        self.connection = False
        self.messages = {}
        self.keepAlive = 2

    def send(self, frame):
        self.sock.send(frame)

    def recv(self, size = 1024):
        while self.connection:
            data = self.sock.recv(size)
            self.parseFrame(data, self)

    def connect(self, name = "", passwd = "", will = 0, willTopic = "", willMessage = "", clean = 0, cliID = "", keepAlive = 2):
        # TODO: above default value should be considered
        self.cleanSession = clean
        self.sock.connect(self.addr)
        self.connection = True
        self.keepAlive = keepAlive
        frame = self.makeFrame(TYPE.CONNECT, 0, 0, 0, name = name, passwd = passwd,
                             will = will, willTopic = willTopic, willMessage = willMessage,
                             clean = clean, cliID = cliID, keepAlive = keepAlive)
        self.sock.send(frame)
        self.recvThread = Thread(target=self.recv)
        self.recvThread.start()
        self.pingThread = Thread(target=self.__pingreq)
        self.pingThread.start()

    def disconnect(self):
        frame = self.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.send(frame)
        self.connection = False
        self.sock.close()
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
        frame = self.makeFrame(TYPE.PUBLISH, dup, qos, retain, topic = topic, message = message, messageID = messageID)
        self.send(frame)

    def initTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive, self.disconnect)

    def __pingreq(self):
        self.timer = Timer(self.keepAlive, self.disconnect)
        while True:
            # Q: continuously send req? or send after receiving resp?
            time.sleep(self.keepAlive)
            if not self.connection:
                break
            self.send(self.makeFrame(TYPE.PINGREQ, 0,0,0))
            self.timer.start()

    def subscribe(self, topics, dup = 0, messageID = 1):
        # topics should be [[topic1, qos1], [topic2, qos2] ...]
        if len(topics) >= 2:
            qos = 1
        elif len(topics) == 1:
            qos = 0

        frame = self.makeFrame(TYPE.SUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)

    def unsubscribe(self, topics, dup = 0, messageID = 1):
        # topics should be [topic1, topic2 ...]
        if len(topics) >= 2:
            qos = 1
        elif len(topics) == 1:
            qos = 0

        frame = self.makeFrame(TYPE.UNSUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)
