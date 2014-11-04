import frame as fm
import socket
from setting import TYPE

class Edge(object):
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.cleanSession = 0

    def send(self, frame):
        self.sock.send(frame)

    def connect(self, name = "", passwd = "", will = "", willTopic = "", willMessage = "", clean = 0, cliId = ""):
        # TODO: above default value should be considered
        self.cleanSession = clean
        self.sock.create_connection((self.host, self.port), 5)
        frame = fm.makeFrame(TYPE.CONNECT, 0, 0, 0, name, passwd, will, willTopic, willMessage, clean, cliId)
        self.sock.send(frame)

    def disconnect(self, name):
        frame = fm.makeFrame(TYPE.DISCONNECT, 0, 0, 0)
        self.sock.send(frame)
        
class Publisher(Edge):
    def __init__(self, host, port):
        super(Publisher, self).__init__(host, port)

    def publish(self, topic, message, dup = 0, qos = 0, retain = 0, messageID = None):
        if (qos == 1 or qos == 2) and messageID == None:
            #error, here?
            pass
        frame = fm.makeFrame(TYPE.PUBLISH, dup, qos, retain, topic = topic, message = message, messageID = messageID)
        self.send(frame)
        # recv something?

class Client(Edge):
    def __init__(self, host, port):
        super(Client, self).__init__(host, port)

    def subscribe(self, topics, dup = 0, qos = 0, messageID = None):
        # topics should be [[topic1, qos1], [topic2, qos2] ...]
        if qos == 0 and len(topics) >= 2:
            # error, when qos == 1, then len(topics) is allowed to be more than or equal to 2
            pass
        if len(topics) >= 2:
            qos = 1 # is this nice?
        frame = fm.makeFrame(TYPE.SUBSCRIBE, dup, qos, 0, topics = topics, messageID = messageID)
        self.send(frame)
        # recv suback

    def unsubscribe(self, topics, dup = 0, qos = 0):
        # topics should be [topic1, topic2 ...]
        if len(topics) >= 2:
            qos = 1
        frame = fm.makeFrame(TYPE.UNSUBSCRIBE, dup, qos, 0, topics = topics)
        self.send(frame)
        # recv unsuback

    def __pingreq(self):
        # Should this be sent automatically ?
        frame = fm.makeFrame(TYPE.PINGREQ, 0,0,0)
        self.send(frame)
        # recv pingresp
