from settings import *
from binascii import hexlify, unhexlify
from util import upackHex, packHex, utfEncode, utfDecode
from settings import TYPE
from settings import ConnectReturn as CR

class Frame(object):
    def __init__(self):
        self.idx = 0

    def getIncrement(self, payload):
        data, idx = utfDecode(payload)
        self.idx += idx
        return data

    def makeFrame(self, t, dup, qos, retain, **kwargs):
        data = ""
        def makeHeader(length):
            #not cool
            byte1 = hexlify(t)[1] + hex(int(str(dup)+bin(qos)[2:].zfill(2)+str(retain), 2))[2:]
            byte2 = "".join([packHex(l) for l in encodeRestLen(length)]) if length else "00"
            return unhexlify(byte1 + byte2)

        def connect():
            # this hard code is not cool
            frame = utfEncode(SUPPORT_PROTOCOLS[0])
            frame += packHex(SUPPORT_PROTOCOL_VERSIONS[0])
            flag = 1 << 7 if kwargs.has_key("name") else 0 << 7 #TODO: there is the case withoug string
            flag |= 1 << 6 if kwargs.has_key("passwd") else 0 << 6
            willData = ""
            if kwargs.has_key("will"):
                flag |= 1 << 5
                flag |= kwargs["will"]["QoS"] << 3
                flag |= 1 << 2
                willData = utfEncode(kwargs["will"]["topic"])
                willData += utfEncode(kwargs["will"]["message"])
            flag |= 1 << 1 if kwargs.has_key("clean") else 0 << 1
            frame += packHex(flag)
            frame += packHex(kwargs["keepAlive"], 4)
            frame += utfEncode(kwargs["cliID"]) if kwargs.has_key("cliID") else ""
            frame += willData
            frame += utfEncode(kwargs["name"]) if kwargs.has_key("name") else ""
            frame += utfEncode(kwargs["passwd"]) if kwargs.has_key("passwd") else ""
            # TODO: save these settings to server, if there is no cliID, then apply the ID from server
            return frame

        def connack():
            frame = "00"
            frame += hexlify(kwargs["code"])
            return frame

        def publish():
            frame = utfEncode(kwargs["topic"])
            frame += packHex(kwargs["messageID"], 4) if qos else ""
            frame += utfEncode(kwargs["message"]) if kwargs.has_key("message") else ""
            return frame

        def puback():
            # for qos == 1
            frame = packHex(kwargs["messageID"], 4)
            return frame

        def pubrec():
            # for qos == 2
            frame = packHex(kwargs["messageID"], 4)
            return frame

        def pubrel():
            # for qos == 2 and response to pubrec
            frame = packHex(kwargs["messageID"], 4)
            return frame

        def pubcomp():
            # for qos == 2 and response to pubrel
            frame = packHex(kwargs["messageID"], 4)
            return frame

        def subscribe():
            frame = packHex(kwargs["messageID"], 4)
            for topic in kwargs["topics"]:
                frame += utfEncode(topic[0])
                frame += packHex(topic[1], 2)
            return frame

        def suback():
            frame = packHex(kwargs["messageID"], 4)
            for q in kwargs["qosList"]:
                frame += packHex(q)
            return frame

        def unsubscribe():
            frame = packHex(kwargs["messageID"], 4)
            for sub in kwargs["topics"]:
                frame += utfEncode(sub)
            return frame

        def unsuback():
            #response to unsubscribe
            frame = packHex(kwargs["messageID"], 4)
            return frame

        if t == TYPE.CONNECT:
            data = connect()
        elif t == TYPE.CONNACK:
            data = connack()
        elif t == TYPE.PUBLISH:
            data = publish()
        elif t == TYPE.PUBACK:
            data = puback()
        elif t == TYPE.PUBREC:
            data = pubrec()
        elif t == TYPE.PUBREL:
            data = pubrel()
        elif t == TYPE.PUBCOMP:
            data = pubcomp()
        elif t == TYPE.SUBSCRIBE:
            data = subscribe()
        elif t == TYPE.SUBACK:
            data = suback()
        elif t == TYPE.UNSUBSCRIBE:
            data = unsubscribe()
        elif t == TYPE.UNSUBACK:
            data = unsuback()
        elif t == TYPE.PINGREQ:
            data = "" # no payload
        elif t == TYPE.PINGRESP:
            data = "" # no payload
        elif t == TYPE.DISCONNECT:
            data = "" # no payload
        else:
            print("undefined type")

        data = unhexlify(data)
        return makeHeader(len(data)) + data

    def parseFrame(self, data, client):
        def parseHeader(header):
            byte1 = upackHex(header[0])
            t = unhexlify(hex((byte1 & 0xf0) >> 4)[2:].zfill(2))
            dub = (byte1 & 0x08) >> 3
            qos = (byte1 & 0x06) >> 1
            retain = byte1 & 0x01
            restLen, idx = decodeRestLen([upackHex(x) for x in header[1:]])
            return t, dub, qos, retain, restLen, idx+1

        def connect(data):
            proto = self.getIncrement(data)
            protoVersion = upackHex(data[self.idx])
            flags = upackHex(data[self.idx + 1])
            keepAlive = upackHex(data[self.idx + 2:self.idx + 4])

            self.idx += 4
            cliId = self.getIncrement(data[self.idx:])
            will = {"QoS": (flags & 0x18) >> 3, "retain": (flags & 0x20) >> 5, "topic": "", "message": ""}
            if flags & 0x04:
                will["topic"] = self.getIncrement(data[self.idx:])
                will["message"] = self.getIncrement(data[self.idx:])
            name = self.getIncrement(data[self.idx:]) if flags & 0x80 else ""
            passwd = self.getIncrement(data[self.idx:]) if flags & 0x40 else ""
            clean = flags & 0x02

            return cliId, name, passwd, will, keepAlive, clean

        def connack(data):
            topicCompress = data[0]
            code = data[1]
            return code

        def publish(data):
            topic = self.getIncrement(data)
            messageID = 1
            if 1 <= qos <= 2:
                messageID = upackHex(data[self.idx:self.idx + 2])
            pubData = self.getIncrement(data[self.idx:]) if len(data[self.idx:]) else ""
            return messageID, qos, topic, pubData

        def puback(data):
            messageID = upackHex(data[:2])
            return messageID

        def pubrec(data):
            messageID = upackHex(data[:2])
            return messageID

        def pubrel(data):
            messageID = upackHex(data[:2])
            return messageID

        def pubcomp(data):
            messageID = upackHex(data[:2])
            return messageID

        def subscribe(data):
            self.idx += 2
            messageID = upackHex(data[:self.idx])
            topics = []
            allowedQoSs = []
            while data[self.idx:]:
                topic = self.getIncrement(data[self.idx:])
                reqQoS = upackHex(data[self.idx])
                topics.append(topic)
                allowedQoSs.append(reqQoS)
                self.idx += 1
            return messageID, topics, allowedQoSs

        def suback(data):
            messageID = upackHex(data[:2])
            allowedQoSs = []
            for q in data[2:]:
                allowedQoSs.append(upackHex(q))
            return messageID, allowedQoSs

        def unsubscribe(data):
            self.idx += 2
            messageID = upackHex(data[:self.idx])
            topics = []
            while data[self.idx:]:
                topic = self.getIncrement(data[self.idx:])
                topics.append(topic)
            return messageID, topics

        def unsuback(data):
            messageID = upackHex(data[:2])
            return messageID

        def pingreq(data):
            pass

        def pingresp(data):
            pass

        def disconnect(data):
            pass

        while data:
            self.idx = 0
            t, dup, qos, retain, length, idx = parseHeader(data)
            if t == TYPE.CONNECT:
                cliId, name, passwd, will, keepAlive, clean = connect(data[idx:idx+length])
                self.setClient(client, cliId, name, passwd, will, keepAlive, clean)

            elif t == TYPE.CONNACK:
                code = connack(data[idx:idx+length])
                if code == CR.ACCEPTED:
                    self.startSession()
                else:
                    print(CR.string(code)) #temporaly just print

            elif t == TYPE.PUBLISH:
                messageID, qos, topic, pubData = publish(data[idx:idx+length])
                if qos == 1:
                    client.send(self.makeFrame(TYPE.PUBACK, 0, 0, 0, messageID = messageID))
                elif qos == 2:
                    client.send(self.makeFrame(TYPE.PUBREC, 0, 0, 0, messageID = messageID))
                    self.setState(["pubrec"], messageID, client)

                if "server.Broker" in str(self):
                    # this should be called only if child class is Broker
                    self.publishAll(client, topic, pubData, messageID, retain)

            elif t == TYPE.PUBACK:
                messageID = puback(data[idx:idx+length])
                self.puback(messageID)

            elif t == TYPE.PUBREC:
                messageID = pubrec(data[idx:idx+length])
                self.pubrec(messageID)
                client.send(self.makeFrame(TYPE.PUBREL, 0, 1, 0, messageID = messageID))
                self.setState(["pubrel"], messageID, client)

            elif t == TYPE.PUBREL:
                messageID = pubrel(data[idx:idx+length])
                client.send(self.makeFrame(TYPE.PUBCOMP, 0, 0, 0, messageID = messageID))
                self.pubrel(messageID)

            elif t == TYPE.PUBCOMP:
                messageID = pubcomp(data[idx:idx+length])
                self.pubcomp(messageID)

            elif t == TYPE.SUBSCRIBE:
                messageID, topics, QoSs = subscribe(data[idx:idx+length])
                self.setTopic(client, topics, QoSs, messageID)
                client.send(self.makeFrame(TYPE.SUBACK, 0, 0, 0, messageID = messageID, qosList = QoSs))

            elif t == TYPE.SUBACK:
                messageID, QoSs = suback(data[idx:idx+length])
                self.setSubscribe(QoSs)

            elif t == TYPE.UNSUBSCRIBE:
                messageID, topics = unsubscribe(data[idx:idx+length])
                self.unsetTopic(client, topics)
                client.send(self.makeFrame(TYPE.UNSUBACK, 0, 0, 0, messageID = messageID))

            elif t == TYPE.UNSUBACK:
                messageID = unsuback(data[idx:idx+length])
                self.unsetSubscribe()

            elif t == TYPE.PINGREQ:
                pingreq(data[idx:idx+length])
                client.send(self.makeFrame(TYPE.PINGRESP, 0, 0, 0))

            elif t == TYPE.PINGRESP:
                pingresp(data[idx:idx+length])
                self.initTimer()

            elif t == TYPE.DISCONNECT:
                disconnect(data[idx:idx+length])
                self.disconnect(client)

            else:
                print("undefined type")
            data = data[idx+length:]

def encodeRestLen(X):
    output = []
    while X > 0:
        digit = X % 128
        X = X // 128
        if X > 0:
            digit |= 0x80
        output.append(digit)
    return output

def decodeRestLen(X):
    multiplier = 1
    value = 0
    idx = 0
    while idx == 0 or X[idx-1] & 0x80:
        value += (X[idx] & 0x7f) * multiplier
        multiplier *= 0x80
        idx += 1
    return value, idx
