import frame as fm
import socket
from settings import TYPE
from threading import Thread, Timer, Event
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
        self.pingEvent = Event()

    def send(self, frame):
        self.sock.send(frame)

    def __recv(self, size = 1024):
        try:
            while self.connection:
                data = self.sock.recv(size)
                self.parseFrame(data, self)
        except Exception as e:
            # TODO: exception should be defined
            print e

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
        # NOTICE: sometimes this is called shoter than the keep alive time,
        #         threading.Timer bug?
        if not self.connection:
            print("connection has already closed %s" % self.ID)
            return
        self.connection = False
        frame = self.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.send(frame)
        self.sock.close()
        print("disconnect %s" % self.ID)

    def publish(self, topic, message, dup = 0, qos = 0, retain = 0, messageID = 1):
        if (qos == 1 or qos == 2) and messageID == 0:
            #error, here
            pass
        if qos == 1 or qos == 2:
            # this stahds for unacknowledged state
            self.setState(["publish", topic, message, qos, retain], messageID, None)
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

    def setState(self, state, messageID, dummy):
        self.messages[messageID] = state

    def resend(self):
        for messageID in self.messages:
            state = self.messages[messageID]
            if state[0] == "publish":
                self.send(self.makeFrame(TYPE.PUBLISH, 1, state[3], state[4], topic = state[1],
                                         message = state[2], messageID = messageID))
            elif state[0] == "pubrec":
                self.send(self.makeFrame(TYPE.PUBREC, 1, 0, 0, messageID = messageID))
            elif state[0] == "pubrel":
                self.send(self.makeFrame(TYPE.PUBREL, 1, 1, 0, messageID = messageID))

    def initTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive, self.disconnect)
        self.pingEvent.set()

    def __pingreq(self):
        self.timer = Timer(self.keepAlive, self.disconnect)
        try:
            while self.connection:
                # Q: continuously send req? or send after receiving resp?
                self.send(self.makeFrame(TYPE.PINGREQ, 0,0,0))
                if not self.timer.is_alive():
                    self.timer.start()
                pingTime = time.time()
                self.pingEvent.wait(self.keepAlive * 2) # Is this timeout appropriate?
                time.sleep(self.keepAlive - (time.time() - pingTime))

        except Exception as e:
            print e, self.ID
            pass

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
