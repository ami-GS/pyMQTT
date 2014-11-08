from settings import *
from binascii import hexlify, unhexlify
from util import upackHex, packHex, utfEncode, utfDecode

willQoS = 3 #temporaly

# TODO: this should be class, and each instance should has cliID, name, etc.. info. 
def makeFrame(t, dup, qos, retain, **kwargs):
    data = ""
    def makeHeader(length):
        #not cool
        byte1 = hexlify(t)[1] + hex(int(str(dup)+bin(qos)[2:].zfill(2)+str(retain), 2))[2:]
        byte2 = "".join([packHex(l) for l in encodeRestLen(length)]) if length else "00"
        return unhexlify(byte1 + byte2)

    def connect():
        # this hard code is not cool
        frame = "0006"
        frame += packHex(CONNECT_PROTOCOL)
        frame += hex(PROTOCOL_VERSION)[2:].zfill(2)
        flag = 1 << 7 if kwargs["name"] else 0 << 7 #TODO: there is the case withoug string
        flag |= 1 << 6 if kwargs["passwd"] else 0 << 6
        flag |= 1 << 5 if kwargs["will"] else 0 << 5 # for future use
        flag |= willQoS << 3 if kwargs["will"] else 0 << 3
        flag |= 1 << 2 if kwargs["will"] else 0 << 2
        flag |= 1 << 1 if kwargs["clean"] else 0 << 1
        frame += packHex(flag)
        frame += packHex(kwargs["keepAlive"], 4)
        frame += utfEncode(kwargs["cliID"]) if kwargs.has_key("cliID") else ""
        frame += utfEncode(kwargs["willTopic"]) if kwargs.has_key("will") else ""
        frame += utfEncode(kwargs["willMessage"]) if kwargs.has_key("will") else ""
        frame += utfEncode(kwargs["name"]) if kwargs.has_key("name") else ""
        frame += utfEncode(kwargs["passwd"]) if kwargs.has_key("passwd") else ""
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
        # looks not cool
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
        data = "" # no payload, I have to manage 'Clean session' flag
    else:
        print("undefined type")

    data = unhexlify(data)
    return makeHeader(len(data)) + data

def parseFrame(data, receiver):
    def parseHeader(header):
        byte1 = upackHex(header[0])
        t = unhexlify(hex((byte1 & 0xf0) >> 4)[2:].zfill(2))
        dub = (byte1 & 0x08) >> 3
        qos = (byte1 & 0x06) >> 1
        retain = byte1 & 0x01
        restLen, idx = decodeRestLen([upackHex(x) for x in header[1:]])
        return t, dub, qos, retain, restLen, idx

    def connect(data):
        # TODO: client object should be made to save these flags
        proto, protoLen = utfDecode(data)
        protoVersion = upackHex(data[protoLen])
        flags = upackHex(data[protoLen + 1])
        keepAlive = upackHex(data[protoLen + 2:protoLen + 4])

        payLoadIdx = protoLen + 4
        cliId, idx = utfDecode(data[payLoadIdx:])
        payLoadIdx += idx
        willTopic, idx = utfDecode(data[payLoadIdx:]) if flags & 0x04 else ("", 0)
        payLoadIdx += idx
        willMessage, idx = utfDecode(data[payLoadIdx:]) if flags & 0x04 else ("", 0)
        payLoadIdx += idx
        name, idx = utfDecode(data[payLoadIdx:]) if flags & 0x80 else ("", 0)
        payLoadIdx += idx
        passwd, idx = utfDecode(data[payLoadIdx:]) if flags & 0x40 else ("", 0)
        payLoadIdx += idx
        clean = flags & 0x02

        receiver.setClient(cliId, name, passwd, willTopic, willMessage, keepAlive, clean)

        return payLoadIdx

    def connack(data):
        topicCompress = data[0]
        code = data[1]

        return  2

    def publish(data):
        topic, topicLen = utfDecode(data)
        messageID = upackHex(data[topicLen:2+topicLen])
        pubData, pubLen = utfDecode(data[2+topicLen:]) if len(data[2+topicLen:]) else "" # correct?
        if qos == 1:
            pass # send puback
        elif qos == 2:
            pass # send pucrec

        if isinstance(receiver, Broker):
            receiver.publish(topic, pubData, messageID)

        return 2 + topicLen + pubLen

    def puback(data):
        messageID = upackHex(data[:2])
        # delete message ?
        return 2

    def pubrec(data):
        messageID = upackHex(data[:2])
        # send pubrel
        return 2

    def pubrel(data):
        messageID = upackHex(data[:2])
        # send pubcomp
        return 2

    def pubcomp(data):
        messageID = upackHex(data[:2])
        # delete message ?
        return 2

    def subscribe(data):
        c = 2
        messageID = upackHex(data[:c])
        while data[c:]:
            topic, topicLen = utfDecode(data[c:])
            reqQoS = upackHex(data[c+topicLen])
            receiver.setTopic([topic, reqQoS])
            c += topicLen + 1
        receiver.suback(messageID)
        return c
        # publish may be sent

    def suback(data):
        c = 2
        messageID = upackHex(data[:c])
        for q in data[2:]:
            allowedQoS = upackHex(q)
            c += 1
        return c

    def unsubscribe(data):
        c = 2
        messageID = upackHex(data[:c])
        while data[c:]:
            topic, topicLen = utfDecode(data[c:])
            receiver.unsetTopic(topic)
            c += topicLen + 1
        receiver.unsuback()
        return c

    def unsuback(data):
        c = 2
        messageID = upackHex(data[:c])
        return c

    def pingreq(data):
        receiver.pingresp()
        return 0

    def pingresp(data):
        return 0

    def disconnect(data):
        receiver.disconnect()
        return 0
        # do something based on clean session info
        # disconnect TCP

    idx = 0
    length = 0
    while data[idx+length:]:
        t, dup, qos, retain, length, i = parseHeader(data[idx:idx+2])
        idx += i + 1
        if t == TYPE.CONNECT:
            idx += connect(data[idx:idx+length])
        elif t == TYPE.CONNACK:
            idx += connack(data[idx:idx+length])
        elif t == TYPE.PUBLISH:
            idx += publish(data[idx:idx+length])
        elif t == TYPE.PUBACK:
            idx += puback(data[idx:idx+length])
        elif t == TYPE.PUBREC:
            idx += pubrec(data[idx:idx+length])
        elif t == TYPE.PUBREL:
            idx += pubrel(data[idx:idx+length])
        elif t == TYPE.PUBCOMP:
            idx += pubcomp(data[idx:idx+length])
        elif t == TYPE.SUBSCRIBE:
            idx += subscribe(data[idx:idx+length])
        elif t == TYPE.SUBACK:
            idx += suback(data[idx:idx+length])
        elif t == TYPE.UNSUBSCRIBE:
            idx += unsubscribe(data[idx:idx+length])
        elif t == TYPE.UNSUBACK:
            idx += unsuback(data[idx:idx+length])
        elif t == TYPE.PINGREQ:
            idx += pingreq(data[idx:idx+length])
        elif t == TYPE.PINGRESP:
            idx += pingresp(data[idx:idx+length])
        elif t == TYPE.DISCONNECT:
            idx += disconnect(data[idx:idx+length])
        else:
            print("undefined type")


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
