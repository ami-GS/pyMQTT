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

    def setClient(self, cliID, name, passwd, willTopic, willMessage, keepAlive):
        self.clients[self.addr] = {"socket":self.sock, "cliID":cliID, "name":name, "passwd":passwd,
                                   "willTopic":willTopic, "willMessage":willMessage,
                                   "keepAlive":keepAlive, "timer":Timer(keepAlive*1.5, self.disconnect)}

    def disconnect(self):
        frame = fm.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        #self.clients[self.addr]["socket"].send(frame)
        self.send(frame)
        self.clients[self.addr]["socket"].close()
        del self.clients[self.addr]
        print "disconnect"

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
        self.clients[self.addr]["socket"].send(frame)
