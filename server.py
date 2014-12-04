import frame as fm
from settings import ConnectReturn as CR
from settings import TYPE
import socket, select
from threading import Timer, Thread
from frame import Frame

class Broker(Frame):
    def __init__(self, host = "127.0.0.1", port = 8888):
        super(Broker, self).__init__()
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.bind((host, port))
        self.host = host
        self.port = port
        self.clients = {}
        self.topics = {}
        self.wills = {}
        self.clientSubscribe = {}
        self.clientIDs = {}
        self.usedMessageIDs = {}
        # NOTICE: keys of topics and clientSubscribe should be synchronized
        self.serv.listen(1)

    def worker(self, client):
        while True:
            data = client.recv(1 << 16)
            self.parseFrame(data, client)
            if not client.connection:
                break
            client.restartTimer()

    def runServer(self):
        while True:
            con, addr = self.serv.accept()
            self.clients[addr] = Client(self, addr, con)
            thread = Thread(target = self.worker, args = (self.clients[addr], ))
            #thread.setDaemon(True) # TODO: if this is daemon, error handling should be implemented in client side
            thread.start()

    def setClient(self, client, cliID, name, passwd, will, keepAlive, clean):
        if not cliID:
            if not clean:
                client.send(self.makeFrame(TYPE.CONNACK, 0, 0, 0, code = CR.R_ID_REJECTED))
                client.disconnect()
                return
            cliID = "unknown" + str(len(self.clients)) # TODO: cliID should be determined in here if no cliID was delivered.

        client.setInfo(cliID, name, passwd, will, keepAlive, clean)
        if cliID in self.clientIDs.keys():
            if clean:
                self.clientIDs.pop(cliID)
            else:
                #TODO: name and passwd validation shuld be here?
                self.resumeSession(client)
        elif not clean:
            self.clientIDs[cliID] = client

        #this shold not be here
        client.send(self.makeFrame(TYPE.CONNACK, 0, 0, 0, code = CR.ACCEPTED))

    def resumeSession(self, client):
        client.resumeSession(self.clientIDs[client.ID])
        for topic in client.subscribe:
            self.clientSubscribe[topic].append(client.getAddr())
        self.clientIDs[client.ID] = client

    def setTopic(self, client, topic, QoS, messageID):
        client.setTopic(topic, QoS)
        if self.topics.has_key(topic) and self.topics[topic]:
            # this is 'retain'
            frame = self.makeFrame(TYPE.PUBLISH, 0, QoS, 1, topic = topic,
                                message = self.topics[topic], messageID = messageID)
            client.send(frame)
            if QoS == 1 or QoS == 2:
                self.setState(["publish", topic, message], messageID + i+1, client)

        if self.clientSubscribe.has_key(topic):
            self.clientSubscribe[topic].append(client.getAddr())
        else:
            self.clientSubscribe[topic] = [client.getAddr()]

    def unsetTopic(self, client, topic):
        if client.getAddr() in self.clientSubscribe[topic]:
            self.clientSubscribe[topic].remove(client.getAddr())
            client.unsetTopic(topic)
        else:
            # TODO: this should be removed in the future
            addr = client.getAddr()
            print("(%s, %d) doesn't exist in %s" % (addr[0], addr[1], topic))

    def disconnect(self, client):
        # when get DISCONNECT packet from client
        client.connection = False
        client.close()
        client.timer.cancel()
        # the address should be removed even if the clean flag is not set.
        for topic in client.subscribe:
            self.clientSubscribe[topic].remove(client.getAddr())
        if client.clean:
            # TODO: correct ?
            self.clients.pop(client.getAddr())

        print("disconnect")

    def publishAll(self, topic, message, messageID = 1, retain = 0):
        if self.clientSubscribe.has_key(topic):
            for i, addrs in enumerate(self.clientSubscribe[topic]):
                client = self.clients[addrs]
                QoS = client.getQoS(topic)
                frame = self.makeFrame(TYPE.PUBLISH, 0, QoS, 0, topic = topic,
                                       message = message, messageID = messageID + i+1)
                client.send(frame)
                if QoS == 1 or QoS == 2:
                    self.setState(["publish", topic, message], messageID + i+1, client)
        else:
            self.clientSubscribe[topic] = []
            self.topics[topic] = ""

        if retain:
            self.topics[topic] = message #TODO: QoS shold also be saved

    def setState(self, state, messageID, client):
        # unacknowledge state
        client.messageState[messageID] = state
        self.usedMessageIDs[messageID] = client

    def puback(self, messageID):
        client = self.usedMessageIDs.pop(messageID)
        client.unsetAcknowledge(messageID)

    def pubrec(self, messageID):
        client = self.usedMessageIDs.pop(messageID)
        client.unsetAcknowledge(messageID)

    def pubrel(self, messageID):
        client = self.usedMessageIDs.pop(messageID)
        client.unsetAcknowledge(messageID)

    def pubcomp(self, messageID):
        client = self.usedMessageIDs.pop(messageID)
        client.unsetAcknowledge(messageID)

class Client():
    def __init__(self, server, addr, sock):
        self.server = server
        self.__addr = addr
        self.__sock = sock
        self.connection = True
        self.will = None

    def setInfo(self, ID, name = "", passwd = "", will = {}, keepAlive = 2, clean = 1):
        self.ID = ID
        self.__name = name
        self.__passwd = passwd
        self.will = will
        self.keepAlive = keepAlive
        self.timer = Timer(keepAlive * 1.5, self.disconnect)
        self.subscribe = {}
        self.clean = clean
        self.messageState = {}

    def resumeSession(self, client):
        self.__name = client.getName()
        self.__passwd = client.getPasswd()
        self.will = client.will #correct?
        self.keepAlive = client.keepAlive
        self.timer = Timer(self.keepAlive * 1.5, self.disconnect)
        self.subscribe = client.subscribe
        self.clean = client.clean
        self.messageState = client.messageState
        self.resend()

    def resend(self):
        for messageID in self.messageState:
            state = self.messageState[messageID]
            if state[0] == "publish":
                QoS = self.getQoS[state[1]]
                self.send(self.server.makeFrame(TYPE.PUBLISH, 1, QoS, 0, topic = state[1],
                                                message = state[2], messageID = messageID))
            elif state[0] == "pubrec":
                self.send(self.server.makeFrame(TYPE.PUBREC, 1, 0, 0, messageID = messageID))
            elif state[0] == "pubrel":
                self.send(self.server.makeFrame(TYPE.PUBREL, 1, 1, 0, messageID = messageID))

    def getAddr(self):
        return self.__addr

    def getSocket(self):
        return self.__sock

    def getName(self):
        return self.__name

    def getPasswd(self):
        return self.__passwd

    def sendWill(self):
        frame = self.server.makeFrame(TYPE.PUBLISH, 0, self.will["QoS"], self.will["retain"],
                                      topic = self.will["topic"], message = self.will["message"], messageID = 1)
        self.send(frame)

    def disconnect(self):
        # when ping packet didn't came within the keepAlive * 1.5 sec
        self.connection = False
        if self.will:
            self.sendWill()
        self.__sock.close()
        if self.clean:
            self.server.clients.pop(self.__addr)
        print("disconnect")

    def unsetAcknowledge(self, messageID):
        self.messageState.pop(messageID)

    def setTopic(self, topic, QoS):
        self.subscribe[topic] = QoS

    def unsetTopic(self, topic):
        if topic in self.subscribe.keys():
            self.subscribe.pop(topic)

    def getQoS(self, topic):
        return self.subscribe[topic]

    def recv(self, num):
        return self.__sock.recv(num)

    def send(self, frame):
        self.__sock.send(frame)

    def close(self):
        self.__sock.close()

    def restartTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive * 1.5, self.disconnect)
        self.timer.start()
