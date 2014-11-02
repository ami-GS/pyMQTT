from settings import *
from binascii import hexlify, unhexlify
from util import upackHex, packHex

willQoS = 3 #temporaly

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
#"".join([packHex(c) for c in CONNECT_PROTOCOL])
        frame += hex(PROTOCOL_VERSION)[2:].zfill(2)
        flag = 1 << 7 if kwargs["name"] else 0 << 7 #TODO: there is the case withoug string
        flag |= 1 << 6 if kwargs["passwd"] else 0 << 6
        flag |= 1 << 5 if kwargs["will"] else 0 << 5 # for future use
        flag |= willQoS << 3 if kwargs["will"] else 0 << 3
        flag |= 1 << 2 if kwargs["will"] else 0 << 2
        flag |= 1 << 1 if kwargs["clean"] else 0 << 1
        frame += packHex(flag)
        frame += packHex(KEEP_ALIVE, 4)
        # connect seems not to use qos, but document write about qos used
        frame += packHex(kwargs["cliID"]) if qos else ""
        frame += "" #TODO: append depends on will
        frame += packHex(kwargs["name"]) if kwargs.has_key("name") else ""
        frame += packHex(kwargs["passwd"]) if kwargs.has_key("passwd") else ""

        return frame

    def connack():
        frame = "00"
        frame += hexlify(kwargs["code"])
        return frame

    def publish():
        pub = kwargs["pub"]
        frame = packHex(len(pub), 4)
        frame += packHex(pub)
        frame += packHex(kwargs["messageID"], 4) if qos else ""
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
        for i in range(len(kwargs["sub"])):
            frame += packHex(len(kwargs["sub"][i]), 4)
            frame += packHex(kwargs["sub"][i])
            frame += packHex(kwargs["qosList"][i], 2)
        return frame

    def suback():
        frame = packHex(kwargs["messageID"], 4)
        for q in kwargs["qosList"]:
            frame += packHex(q)
        return frame

    def unsubscribe():
        frame = packHex(kwargs["messageID"], 4)
        for sub in kwargs["sub"]:
            frame += packHex(len(sub[0]), 4)
            frame += "".join([packHex(c) for c in sub])
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

def parseFrame(data):
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
        ptoroLen = upackHex(data[:2])
        proto = data[2:8]
        protoVersion = upackHex(data[8])
        flags = upackHex(data[9])
        keepAlive = upackHex(data[10:11])

        # ? cliID = data[12:]

        if flags & 0x80:
            pass#name
        if flags & 0x40:
            pass#passwd
        if flags & 0x04:
            pass#willTopic
            #willMessage
        if flags & 0x02:
            pass
            # for clean session
        #if flags & 0x01:

    def connack(data):
        topicCompress = data[0]
        code = data[1]

    def publish(data):
        topicLen = upackHex(data[:2])
        topic = data[2:2+topicLen]
        messageID = upackHex(data[2+topicLen:4+topicLen])
        pubData = data[4+topicLen:] if len(data[4+topicLen:]) else "" # correct?
        if qos == 1:
            pass # send puback
        elif qos == 2:
            pass # send pucrec

    def puback(data):
        messageID = upackHex(data[:2])
        # delete message ?

    def pubrec(data):
        messageID = upackHex(data[:2])
        # send pubrel

    def pubrel(data):
        messageID = upackHex(data[:2])
        # send pubcomp

    def pubcomp(data):
        messageID = upackHex(data[:2])
        # delete message ?

    def subscribe(data):
        messageID = upackHex(data[:2])
        data = data[2:]
        while data:
            topicLen = upackHex(data[:2])
            topic = data[2:2+topicLen]
            reqQos = upackHex(data[2+topicLen])
            # do something
            data = data[3+topicLen:]

        # publish may be sent
        # send suback

    def suback(data):
        messageID = upackHex(data[:2])
        for q in data[2:]:
            allowedQoS = upackHex(q)
            pass # do something

    def unsubscribe(data):
        messageID = upackHex(data[:2])
        data = data[2:]
        while data:
            topicLen = upackHex(data[:2])
            topic = data[2:2+topicLen]
            # do something
            data = data[2+topicLen:]
        # send unsuback

    def unsuback(data):
        messageID = upackHex(data[:2])

    def pingreq(data):
        pass
        # send pingresp

    def pingresp(data):
        pass

    def disconnect(data):
        # do something based on clean session info
        # disconnect TCP
        pass

    t, dup, qos, retain, length, idx = parseHeader(data[:2])
    data = data[1+idx:]

    if t == TYPE.CONNECT:
        connect(data)
    elif t == TYPE.CONNACK:
        connack(data)
    elif t == TYPE.PUBLISH:
         publish(data)
    elif t == TYPE.PUBACK:
         puback(data)
    elif t == TYPE.PUBREC:
         pubrec(data)
    elif t == TYPE.PUBREL:
         pubrel(data)
    elif t == TYPE.PUBCOMP:
         pubcomp(data)
    elif t == TYPE.SUBSCRIBE:
         subscribe(data)
    elif t == TYPE.SUBACK:
         suback(data)
    elif t == TYPE.UNSUBSCRIBE:
         unsubscribe(data)
    elif t == TYPE.UNSUBACK:
         unsuback(data)
    elif t == TYPE.PINGREQ:
        pingreq(data)
    elif t == TYPE.PINGRESP:
         pingresp(data)
    elif t == TYPE.DISCONNECT:
         disconnect(data)
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
