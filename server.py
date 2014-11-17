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
        # NOTICE: keys of topics and clientSubscribe should be synchronized

    def worker(self, con, addr):
        data = "dummy"
        while len(data):
            data = con.recv(1 << 16)
            self.parseFrame(data, con, addr)
            if self.clients.has_key(addr):
                self.clients[addr].restartTimer()

    def runServer(self):
        self.serv.listen(1)
        threadNumber = 0
        self.threads = []
        while True:
            con, addr = self.serv.accept()
            thread = Thread(target = self.worker, args = (con, addr, ))
            thread.start()

    def setClient(self, con, addr, cliID, name, passwd, will, keepAlive, clean):
        self.clients[addr] = Client(self, addr, con, cliID, name,
                                    passwd, will, keepAlive, clean)

    def setTopic(self, addr, topicQoS, messageID):
        self.clients[addr].subscribe.append(topicQoS)

        if self.topics.has_key(topicQoS[0]) and self.topics[topicQoS[0]]:
            # this is 'retain'
            frame = self.makeFrame(TYPE.PUBLISH, 0, topicQoS[1], 1, topic = topicQoS[0],
                                   message = self.topics[topicQoS[0]], messageID = messageID)
            self.clients[addr].send(frame)

        if self.clientSubscribe.has_key(topicQoS[0]):
            self.clientSubscribe[topicQoS[0]].append([addr, topicQoS[1]])
        else:
            self.clientSubscribe[topicQoS[0]] = [[addr, topicQoS[1]]]

    def unsetWill(self):
        #when
        pass

    def sendWill(self, frame):
        pass # send willFrame to clients ?

    def unsetTopic(self, addr, topic):
        # not cool
        self.clients[addr].unsetTopic(topic)
        self.clientSubscribe[topic].remove(self.clientSubscribe[topic][[a[0] for a in self.clientSubscribe[topic]].index(addr)])

    def disconnect(self, addr):
        # when get DISCONNECT packet from client
        self.clients[addr].sock.close()
        if self.clients[addr].clean:
            # TODO: correct ?
            self.clients.pop(addr)
        print "disconnect"

    def publish(self, topic, message, messageID = 1, retain = 0):
        if self.topics.has_key(topic):
            for client in self.topics[topic]:
                frame = self.makeFrame(TYPE.PUBLISH, 0, client[1], 0, topic = topic,
                                     message = message, messageID = messageID)
                self.clients[client[0]].send(frame) # TODO: send function should be unified
        else:
            self.topics[topic] = ""

        if retain:
            self.topics[topic] = message

class Client():
    def __init__(self, server, addr, sock, cliID = "", name = "",
                 passwd = "", will = {}, keepAlive = 2, clean = 1):
        self.server = server
        self.addr = addr
        self.sock = sock
        if not cliID:
            cliID = "random" # TODO: cliID should be determined in here if no cliID was delivered.
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
        frame = self.server.makeFrame(TYPE.PUBLISH, 0, self.will["QoS"], self.will["retain"],
                             topic = self.will["topic"], message = self.will["message"], messageID = 1)
        self.sendWill(frame)
        self.sock.close()
        self.server.clients.pop(self.addr)
        print "disconnect"

    def unsetTopic(self, topic):
        self.subscribe.remove(self.subscribe[[t[0] for t in self.subscribe].index(topic)])

    def send(self, frame):
        self.sock.send(frame)

    def restartTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive * 1.5, self.disconnect)
        self.timer.start()
