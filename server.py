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
                self.clients[self.addr]["timer"].cancel()
                self.clients[self.addr]["timer"] = Timer(self.clients[self.addr]["keepAlive"]*1.5, self.disconnect)
                self.clients[self.addr]["timer"].start()

    def setClient(self, cliID, name, passwd, willTopic, willMessage, keepAlive, clean):
        self.clients[self.addr] = {"socket":self.sock, "cliID":cliID, "name":name, "passwd":passwd,
                                   "willTopic":willTopic, "willMessage":willMessage, "clean":clean,
                                   "keepAlive":keepAlive, "timer":Timer(keepAlive*1.5, self.disconnect),
                                   "subscribe":[]}

    def setWill(self, topic, message, QoS, retain):
        self.clients[self.addr]["subscribe"].append([topic, QoS])
        self.wills[self.clients[self.addr]["cliID"]] = [topics, message, QoS, retain]

    def unsetWill(self):
        self.wills.pop([self.clients[self.addr]["cliID"]])

    def setTopic(self, topicQoS, messageID):
        self.clients[self.addr]["subscribe"].append(topicQoS)

        if self.clientSubscribe.has_key(topicQoS[0]):
            self.clientSubscribe[topicQoS[0]].append([self.addr, topicQoS[1]])
            if self.topics[topicQoS[0]]:
                frame = fm.makeFrame(TYPE.PUBLISH, 0, topicOoS[1], 1, topic = topic,
                                     message = self.topics[topicQoS[0]], messageID = messageID)
                self.send(frame)
        else:
            self.clientSubscribe[topicQoS[0]] = [[self.addr, topicQoS[1]]]

    def unsetTopic(self, topic):
        # not cool
        self.clients["subscribe"].remove(self.clients["subscribe"][[t[0] for t in self.clients["subscribe"]].index(topic)])
        self.topicQoS[topic].remove(self.topicQoS[[addr[0] for addr in self.TopicQoS[topic]].index(self.addr)])

    def disconnect(self):
        if self.wills.has_key(self.clients[self.addr]["cliID"]):
            will = self.wills[self.clients[self.addr]["cliID"]]
            frame = fm.makeFrame(TYPE.PUBLISH, 0, will[2], will[3],
                                 topic = will[0], message = will[1], messageID = 1)
            # TODO: send to ??
        frame = fm.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.send(frame)
        self.clients[self.addr]["socket"].close()
        if self.clients[self.addr]["clean"]:
            self.clients.pop(self.addr)
        print "disconnect"

    def suback(self, messageID):
        frame = fm.makeFrame(TYPE.SUBACK, 0, 0, 0, messageID = messageID,
                             qosList = [topic[1] for topic in self.clients[self.addr]["subscribe"]])
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
        frame = fm.makeFrame(TYPE.PINGRESP, 0, 0, 0)
        self.send(frame)

    def publish(self, topic, message, messageID = 1, retain = 0):
        if self.topics.has_key(topic):
            for client in self.topics[topic]:
                frame = fm.makeFrame(TYPE.PUBLISH, 0, client[1], 0, topic = topic,
                                     message = message, messageID = messageID)
                self.clients[client[0]]["socket"].send(frame) # TODO: send function should be unified
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
        self.clients[self.addr]["socket"].send(frame)
