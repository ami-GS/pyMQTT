import frame as fm
from settings import ConnectReturn as CR
from settings import TYPE
import socket
from threading import Timer

class Broker():
    def __init__(self, host = "127.0.0.1", port = 8888):
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.bind((host, port))
        self.host = host
        self.port = port
        self.clients = {}
        self.topics = {}
        self.wills = {}
        self.clientSubscribe = {}
        # NOTICE: keys of topics and clientSubscribe should be synchronized

    def runServer(self):
        self.serv.listen(1)
        while True:
            self.sock, self.addr = self.serv.accept()
            data = "dummy"
            while len(data):
                data = self.sock.recv(1 << 16)
                fm.parseFrame(data, self)
                if self.clients.has_key(self.addr):
                    self.clients[self.addr].restartTimer() #when DISCONNECT frame coms, then error might occur because the socket is already closed

    def setClient(self, cliID, name, passwd, will, keepAlive, clean):
        self.clients[self.addr] = Client(self, self.addr, self.sock, cliID,
                                         name, passwd, will, keepAlive, clean)

    def setTopic(self, topicQoS, messageID):
        self.clients[self.addr].subscribe.append(topicQoS)

        if self.clientSubscribe.has_key(topicQoS[0]):
            self.clientSubscribe[topicQoS[0]].append([self.addr, topicQoS[1]])
            if self.topics[topicQoS[0]]:
                frame = fm.makeFrame(TYPE.PUBLISH, 0, topicOoS[1], 1, topic = topic,
                                     message = self.topics[topicQoS[0]], messageID = messageID)
                self.send(frame)
        else:
            self.clientSubscribe[topicQoS[0]] = [[self.addr, topicQoS[1]]]

    def unsetWill(self):
        #when
        pass

    def sendWill(self, frame):
        pass # send willFrame to clients ?

    def unsetTopic(self, topic):
        # not cool
        self.clients[self.addr].unsetTopic(topic)
        self.topicQoS[topic].remove(self.topicQoS[[addr[0] for addr in self.TopicQoS[topic]].index(self.addr)])

    def disconnect(self):
        # when get DISCONNECT packet from client
        self.clients[self.addr].sock.close()
        if self.clients[self.addr].clean:
            # TODO: correct ?
            self.clients.pop(self.addr)
        print "disconnect"

    def suback(self, messageID):
        # this looks mistake, the qosList should contain only subscribed QoSs
        frame = fm.makeFrame(TYPE.SUBACK, 0, 0, 0, messageID = messageID,
                             qosList = [topic[1] for topic in self.clients[self.addr].subscribe])
        self.send(frame)

    def unsuback(self, messageID):
        frame = fm.makeFrame(TYPE.UNSUBACK, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def connack(self):
        frame = fm.makeFrame(TYPE.CONNACK, 0, 0, 0, code = CR.ACCEPTED)
        self.send(frame)

    def puback(self, messageID):
        frame = fm.makeFrame(TYPE.PUBACK, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def pubrec(self, messageID):
        frame = fm.makeFrame(TYPE.PUBREC, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def pubrel(self, messageID):
        frame = fm.makeFrame(TYPE.PUBREL, 0, 1, 0, messageID = messageID)
        self.send(frame)

    def pubcomp(self, messageID):
        frame = fm.makeFrame(TYPE.PUBCOMP, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def pingresp(self):
        self.clients[self.addr].pingresp()

    def publish(self, topic, message, messageID = 1, retain = 0):
        if self.topics.has_key(topic):
            for client in self.topics[topic]:
                frame = fm.makeFrame(TYPE.PUBLISH, 0, client[1], 0, topic = topic,
                                     message = message, messageID = messageID)
                self.clients[client[0]].send(frame) # TODO: send function should be unified
        else:
            self.topics[topic] = ""

        if retain:
            self.topics[topic] = message

    def pubrel(self, dup = 0, messageID = 1):
        # dup should be zero ?
        frame = fm.makeFrame(TYPE.PUBREL, dup, 1, 0, messageID = messageID)
        self.send(frame)

    def pubcomp(self, messgeID = 1):
        frame = fm.makeFrame(TYPE.PUBCOMP, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def send(self, frame):
        self.clients[self.addr].send(frame)

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
        self.cleanSession = clean

    def sendWill(self, frame):
        self.server.sendWill(frame)

    def disconnect(self):
        # when ping packet didn't came within the keepAlive * 1.5 sec
        frame = fm.makeFrame(TYPE.PUBLISH, 0, self.will["QoS"], self.will["retain"],
                             topic = self.will["topic"], message = self.will["message"], messageID = 1)
        self.sendWill(frame)
        frame = fm.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.send(frame)
        self.sock.close()
        self.server.clients.pop(self.addr)

    def pingresp(self):
        frame = fm.makeFrame(TYPE.PINGRESP, 0, 0, 0)
        self.send(frame)

    def unsetTopic(self, topic):
        self.subscribe.remove(self.subscribe[[t[0] for t in self.subscribe].index(topic)])

    def send(self, frame):
        self.sock.send(frame)

    def restartTimer(self):
        self.timer.cancel()
        self.timer = Timer(self.keepAlive * 1.5, self.disconnect)
        self.timer.start()
