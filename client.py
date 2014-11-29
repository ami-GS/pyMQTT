import frame as fm
import socket
from settings import TYPE
from threading import Thread, Timer
import time
from frame import Frame

# TODO: multi message sender should be implemented (now single)

class Client(Frame):
    def __init__(self, addr, ID = ""):
        super(Client, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = addr
        self.ID = ID
        self.cleanSession = 0
        self.pingThread = None
        self.connection = False
        self.messages = {}
        self.keepAlive = 2
        self.subscribes = {}
        self.subTmp = []
        self.unsubTmp = []

    def send(self, frame):
        self.sock.send(frame)

    def __recv(self, size = 1024):
        while self.connection:
            data = self.sock.recv(size)
            self.parseFrame(data, self)

    def connect(self, name = "", passwd = "", will = {}, clean = 0, keepAlive = 2):
        # TODO: above default value should be considered
        self.cleanSession = clean
        self.sock.connect(self.addr)
        self.connection = True
        self.keepAlive = keepAlive
        self.recvThread = Thread(target=self.__recv)
        self.recvThread.start()
        frame = self.makeFrame(TYPE.CONNECT, 0, 0, 0, name = name, passwd = passwd,
                             will = will, clean = clean, cliID = self.ID, keepAlive = keepAlive)
        self.send(frame)

    def startSession(self):
        self.pingThread = Thread(target=self.__pingreq)
        self.pingThread.start()

    def disconnect(self):
        if not self.connection:
            print("connection has already closed")
            return
        self.connection = False
        frame = self.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.send(frame)
        self.sock.close()
        print("disconnect")

    def publish(self, topic, message, dup = 0, qos = 0, retain = 0, messageID = 1):
        if (qos == 1 or qos == 2) and messageID == 0:
            #error, here
            pass
        if qos == 1 or qos == 2:
            # this stahds for unacknowledged state
            self.messages[messageID] = ["publish", topic, message]
        elif (qos == 0 or qos == 2) and dup:
            print("Warning: DUP flag should be 0 if QoS is set as %d" % qos)
            dup = 0

        frame = self.makeFrame(TYPE.PUBLISH, dup, qos, retain, topic = topic, message = message, messageID = messageID)
        self.send(frame)

    def puback(self, messageID):
        self.messages.pop(messageID)

    def pubrec(self, messageID):
        self.messages.pop(messageID)

    def pubcomp(self, messageID):
        self.messages.pop(messageID)

    def setUnacknowledged(self, messageID):
        self.messages[messageID] = ["pubrel"]

    def initTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive, self.disconnect)

    def __pingreq(self):
        self.timer = Timer(self.keepAlive, self.disconnect)
        while self.connection:
            # Q: continuously send req? or send after receiving resp?
            self.send(self.makeFrame(TYPE.PINGREQ, 0,0,0))
            self.timer.start()
            time.sleep(self.keepAlive)

    def subscribe(self, topics, dup = 0, messageID = 1):
        # topics should be [[topic1, qos1], [topic2, qos2] ...]
        if len(topics) >= 2:
            qos = 1
        elif len(topics) == 1:
            qos = 0

        frame = self.makeFrame(TYPE.SUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)
        self.subTmp.append(topics)

    def setSubscribe(self, QoSs):
        tmp = self.subTmp.pop(0)
        for i in range(len(QoSs)):
            self.subscribes[tmp[i][0]] = QoSs[i]

    def unsubscribe(self, topics, dup = 0, messageID = 1):
        # topics should be [topic1, topic2 ...]
        if len(topics) >= 2:
            qos = 1
        elif len(topics) == 1:
            qos = 0

        frame = self.makeFrame(TYPE.UNSUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)
        self.unsubTmp.append(topics)

    def unsetSubscribe(self):
        tmp = self.unsubTmp.pop(0)
        for topic in tmp:
            self.subscribes.pop(topic)
