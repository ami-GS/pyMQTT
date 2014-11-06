import frame as fm
from settings import ConnectReturn as CR
from settings import TYPE
import socket

class Broker():
    def __init__(self, host = "127.0.0.1", port = 8888):
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.bind((host, port))
        self.host = host
        self.port = port
        self.clients = {}

    def runServer(self):
        self.serv.listen(1)
        while True:
            self.sock, self.addr = self.serv.accept()
            data = "dummy"
            while len(data):
                data = self.sock.recv(1 << 16)
                fm.parseFrame(data, self)

    def setClient(self, cliId, name, passwd, willTopic, willMessage, keepAlive):
        self.clients[cliId] = {"socket":self.sock, "name":name, "passwd":passwd,
                               "willTopic":willTopic, "willMessage":willMessage, "keepAlive":keepAlive}

    def removeClient(self):
        pass

    def connack(self):
        frame = fm.makeFrame(TYPE.CONNACK, 0, 0, 0, code = CR.ACCEPTED)
        self.send(frame)

    def puback(self, messageID):
        frame = fm.makeFrame(TYPE.PUBACK, 0, 0, 0, messageID = messageID)
        self.send(frame)

    def pingresp(self):
        frame = fm.makeFrame(TYPE.PINGRESP, 0, 0, 0)
        self.send(frame)

    def publish(self, topic, message):
        #search client which waiting the topic ?
        pass

    def send(self, frame):
        self.sock.send(frame)
