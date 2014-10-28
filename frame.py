from settings import TYPE
from binascii import hexlify

def makeHeader(t, dup, qos, retain, length):
    byte1 = hex(t)[2:] + hex(int(str(dup)+bin(qos)[2:].zfill(2)+str(retain), 2))[2:]
    h = hex(length)[2:]
    byte2 = "".join([hex(l)[2:].zfill(2) for l in encodeRestLen(length)])
    return byte1 + byte2

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
