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
        self.clientIDs = []
        # NOTICE: keys of topics and clientSubscribe should be synchronized
        self.serv.listen(1)

    def worker(self, client):
        while True:
            data = client.recv(1 << 16)
            self.parseFrame(data, client)
            if client.connection:
                client.restartTimer()
            else:
                break

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

        if cliID in self.clientIDs:
            #TODO: resume session here
            if clean:
                self.clientIDs.remove(cliID)

        if not clean:
            self.clientIDs.append(cliID)

        client.setInfo(cliID, name, passwd, will, keepAlive, clean)

    def setTopic(self, client, topicQoS, messageID):
        client.setTopic(topicQoS)

        if self.topics.has_key(topicQoS[0]) and self.topics[topicQoS[0]]:
            # this is 'retain'
            frame = self.makeFrame(TYPE.PUBLISH, 0, topicQoS[1], 1, topic = topicQoS[0],
                                message = self.topics[topicQoS[0]], messageID = messageID)
            client.send(frame)

        if self.clientSubscribe.has_key(topicQoS[0]):
            self.clientSubscribe[topicQoS[0]].append([client.addr, topicQoS[1]])
        else:
            self.clientSubscribe[topicQoS[0]] = [[client.addr, topicQoS[1]]]

    def unsetWill(self):
        #when
        pass

    def sendWill(self, frame):
        pass # send willFrame to clients ?

    def unsetTopic(self, client, topic):
        # not cool
        client.unsetTopic(topic)
        self.clientSubscribe[topic].remove(self.clientSubscribe[topic][[a[0] for a in self.clientSubscribe[topic]].index(client.addr)])

    def disconnect(self, client):
        # when get DISCONNECT packet from client
        client.connection = False
        client.sock.close()
        client.timer.cancel()
        if client.clean:
            # TODO: correct ?
            for topic in client.subscribe:
                self.unsetTopic(client, topic)
            self.clients.pop(client.addr)

        print("disconnect")

    def publish(self, topic, message, messageID = 1, retain = 0):
        if self.clientSubscribe.has_key(topic):
            for client in self.clientSubscribe[topic]:
                frame = self.makeFrame(TYPE.PUBLISH, 0, client[1], 0, topic = topic,
                                       message = message, messageID = messageID)
                self.clients[client[0]].send(frame)
        else:
            self.clientSubscribe[topic] = []
            self.topics[topic] = ""

        if retain:
            self.topics[topic] = message #TODO: QoS shold also be saved

class Client():
    def __init__(self, server, addr, sock):
        self.server = server
        self.addr = addr
        self.sock = sock
        self.connection = True
        self.will = None

    def setInfo(self, cliID, name = "", passwd = "", will = {}, keepAlive = 2, clean = 1):
        self.cliID = cliID
        self.name = name
        self.passwd = passwd
        self.will = will
        self.keepAlive = keepAlive
        self.timer = Timer(keepAlive * 1.5, self.disconnect)
        self.subscribe = []
        self.clean = clean

    def sendWill(self, frame):
        self.server.sendWill(frame)

    def disconnect(self):
        # when ping packet didn't came within the keepAlive * 1.5 sec
        self.connection = False
        if self.will:
            # TODO: send message if there is will
            frame = self.server.makeFrame(TYPE.PUBLISH, 0, self.will["QoS"], self.will["retain"],
                                          topic = self.will["topic"], message = self.will["message"], messageID = 1)
            self.sendWill(frame)
        self.sock.close()
        self.server.clients.pop(self.addr)
        print("disconnect")

    def setTopic(self, topicQoS):
        self.subscribe.append(topicQoS)

    def unsetTopic(self, topic):
        self.subscribe.remove(self.subscribe[[t[0] for t in self.subscribe].index(topic)])

    def recv(self, num):
        return self.sock.recv(num)

    def send(self, frame):
        self.sock.send(frame)

    def restartTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive * 1.5, self.disconnect)
        self.timer.start()
