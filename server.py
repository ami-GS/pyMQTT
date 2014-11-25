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

        if cliID in self.clientIDs:
            #TODO: resume session here
            if clean:
                self.clientIDs.remove(cliID)

        if not clean:
            self.clientIDs.append(cliID)

        client.setInfo(cliID, name, passwd, will, keepAlive, clean)

    def setTopic(self, client, topic, QoS, messageID):
        client.setTopic(topic, QoS)

        if self.topics.has_key(topic) and self.topics[topic]:
            # this is 'retain'
            frame = self.makeFrame(TYPE.PUBLISH, 0, QoS, 1, topic = topic,
                                message = self.topics[topic], messageID = messageID)
            client.send(frame)

        if self.clientSubscribe.has_key(topic):
            self.clientSubscribe[topic].append(client.addr)
        else:
            self.clientSubscribe[topic] = [client.addr]

    def unsetTopic(self, client, topic):
        if client.addr in self.clientSubscribe[topic]:
            self.clientSubscribe[topic].remove(client.addr)
        else:
            # TODO: this should be removed in the future
            print("(%s, %d) doesn't exist in %s" % (client.addr[0], client.addr[1], topic))

    def disconnect(self, client):
        # when get DISCONNECT packet from client
        client.connection = False
        client.sock.close()
        client.timer.cancel()
        if client.clean:
            # TODO: correct ?
            for topic in client.subscribe:
                self.unsetTopic(client, topic.keys()[0])
            self.clients.pop(client.addr)

        print("disconnect")

    def publish(self, topic, message, messageID = 1, retain = 0):
        if self.clientSubscribe.has_key(topic):
            for client in self.clientSubscribe[topic]:
                frame = self.makeFrame(TYPE.PUBLISH, 0, self.clients[client].getQoS(topic), 0,
                                       topic = topic, message = message, messageID = messageID)
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

    def sendWill(self):
        frame = self.server.makeFrame(TYPE.PUBLISH, 0, self.will["QoS"], self.will["retain"],
                                      topic = self.will["topic"], message = self.will["message"], messageID = 1)
        self.send(frame)

    def disconnect(self):
        # when ping packet didn't came within the keepAlive * 1.5 sec
        self.connection = False
        if self.will:
            self.sendWill()
        self.sock.close()
        if self.clean:
            self.server.clients.pop(self.addr)
        print("disconnect")

    def setTopic(self, topic, QoS):
        self.subscribe.append({topic: QoS})

    def getQoS(self, topic):
        return self.subscribe[topic]

    def unsetTopic(self, topic):
        self.subscribe.pop(topic)

    def recv(self, num):
        return self.sock.recv(num)

    def send(self, frame):
        self.sock.send(frame)

    def restartTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive * 1.5, self.disconnect)
        self.timer.start()
