from frame import makeFrame, parseFrame
from settings import TYPE
from settings import ConnectReturn as CR
from binascii import hexlify, unhexlify

frames = []

frames.append(hexlify(makeFrame(TYPE.CONNECT, 1,1,1, name = "daiki", passwd = "10!", will = 1,
                                willTopic = "will/u", willMessage = "willwill", clean = 1, cliID = "daiki-aminaka")))
frames.append(hexlify(makeFrame(TYPE.CONNACK, 1,1,1, code = CR.ACCEPTED)))
frames.append(hexlify(makeFrame(TYPE.PUBLISH, 1,1,1, topic = "a/u", message = "publishMesse", messageID = 15)))
frames.append(hexlify(makeFrame(TYPE.PUBACK, 1,1,1, messageID = 15)))
frames.append(hexlify(makeFrame(TYPE.PUBREC, 1,1,1, messageID = 15)))
frames.append(hexlify(makeFrame(TYPE.PUBREL, 1,1,1, messageID = 15)))
frames.append(hexlify(makeFrame(TYPE.PUBCOMP, 1,1,1, messageID = 15)))
frames.append(hexlify(makeFrame(TYPE.SUBSCRIBE, 1,1,1, messageID = 15, sub = ["d/a", "d/c", "d/k"], qosList = [1, 2, 0])))
frames.append(hexlify(makeFrame(TYPE.SUBACK, 1,1,1, messageID = 15, qosList = [1,2,0])))
frames.append(hexlify(makeFrame(TYPE.UNSUBSCRIBE, 1,1,1, messageID = 15, sub = ["d/a", "d/c", "d/k"])))
frames.append(hexlify(makeFrame(TYPE.UNSUBACK, 1,1,1, messageID = 15)))
frames.append(hexlify(makeFrame(TYPE.PINGREQ, 1,1,1)))
frames.append(hexlify(makeFrame(TYPE.PINGRESP, 1,1,1)))
frames.append(hexlify(makeFrame(TYPE.DISCONNECT, 1,1,1)))

for frame in frames:
    parseFrame(unhexlify(frame))
