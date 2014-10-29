from settings import *
from binascii import hexlify, unhexlify

willQoS = 3 #temporaly

def makeFrame(t, dup, qos, retain, **kwargs):
    data = ""
    def makeHeader(length):
        #not cool
        byte1 = hexlify(t)[1] + hex(int(str(dup)+bin(qos)[2:].zfill(2)+str(retain), 2))[2:]
        byte2 = "".join([hex(l)[2:].zfill(2) for l in encodeRestLen(length)])
        return unhexlify(byte1 + byte2)

    def connect():
        # this hard code is not cool
        frame = "0006"
        frame += "".join([hex(ord(c))[2:].zfill(2) for c in CONNECT_PROTOCOL])
        frame += hex(PROTOCOL_VERSION)[2:].zfill(2)
        flag = 1 << 7 if kwargs["name"] else 0 << 7 #TODO: there is the case withoug string
        flag |= 1 << 6 if kwargs["passwd"] else 0 << 6
        flag |= 1 << 5 if kwargs["will"] else 0 << 5 # for future use
        flag |= willQoS << 3 if kwargs["will"] else 0 << 3
        flag |= 1 << 2 if kwargs["will"] else 0 << 2
        flag |= 1 << 1 if kwargs["clean"] else 0 << 1
        frame += hex(flag)[2:].zfill(2)
        frame += hex(KEEP_ALIVE)[2:].zfill(4)
        # connect seems not to use qos, but document write about qos used
        frame += "".join([hex(ord(c))[2:].zfill(2) for c in "cliID"]) if qos else ""
        frame += "" #TODO: append depends on will
        frame += "".join([hex(ord(c))[2:].zfill(2) for c in kwargs["name"]]) if kwargs.has_key("name") else ""
        frame += "".join([hex(ord(c))[2:].zfill(2) for c in kwargs["passwd"]]) if kwargs.has_key("passwd") else ""
        return frame

    def connack():
        frame = "00"
        frame += hexlify(kwargs["code"])
        return frame

    def publish():
        pub = kwargs["pub"]
        frame = hex(len(pub))[2:].zfill(4)
        frame += "".join([hex(ord(c))[2:].zfill(2) for c in  pub])
        frame += hex(kwargs["messageID"])[2:].zfill(4) if qos else ""
        return frame

    def puback():
        # for qos == 1
        frame = hex(kwargs["messageID"])[2:].zfill(4)
        return frame

    def pubrec():
        # for qos == 2
        frame = hex(kwargs["messageID"])[2:].zfill(4)
        return frame

    def pubrel():
        # for qos == 2 and response to pubrec
        frame = hex(kwargs["messageID"])[2:].zfill(4)
        return frame

    def pubcomp():
        # for qos == 2 and response to pubrel
        frame = hex(kwargs["messageID"])[2:].zfill(4)
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
        pass
    elif t == TYPE.SUBACK:
        pass
    elif t == TYPE.UNSUBSCRIBE:
        pass
    elif t == TYPE.UNSUBACK:
        pass
    elif t == TYPE.PINGREQ:
        pass
    elif t == TYPE.PINGRESP:
        pass
    elif t == TYPE.DISCONNECT:
        pass
    else:
        print("undefined type")

    data = unhexlify(data)
    return makeHeader(len(data)) + data



def parseHeader(header):
    byte1 = int(hexlify(header[0]), 16)
    t = (byte1 & 0xf0) >> 4
    dub = (byte1 & 0x08) >>3
    qos = (byte1 & 0x06) >> 1
    retain = byte1 & 0x01
    restLen = decodeRestLen([int(hexlify(x), 16) for x in header[1:]])
    return t, dub, qos, retain, restLen

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
    return value
