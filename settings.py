SUPPORT_PROTOCOL_VERSIONS = [3, 4]
SUPPORT_PROTOCOLS = ["MQIsdp" ,"MQTT"]

class TYPE():
    R_0 = "\x00"
    CONNECT = "\01"
    CONNACK = "\x02"
    PUBLISH = "\x03"
    PUBACK = "\x04"
    PUBREC = "\x05"
    PUBREL = "\x06"
    PUBCOMP = "\x07"
    SUBSCRIBE = "\x08"
    SUBACK = "\x09"
    UNSUBSCRIBE = "\x0a"
    UNSUBACK = "\x0b"
    PINGREQ  = "\x0c"
    PINGRESP = "\x0d"
    DISCONNECT = "\x0e"
    R_15 = "\x0f"

class ConnectReturn():
    ACCEPTED = "\x00"
    R_UNACCEPTABLE_PROTOCOL_VERSION = "\x01"
    R_ID_REJECTED = "\02"
    R_SERVER_UNAVAILABLE = "\x03"
    R_BAD_NAME_PASS = "\04"
    R_NOT_AUTHORIZED = "\x05"

    @classmethod
    def string(cls, num):
        if num == cls.ACCEPTED:
            return "CONNECTION ACCEPTED"
        elif num == cls.R_UNACCEPTABLE_PROTOCOL_VERSION:
            return "UNACCEPTABLE PROTOCOL VERSION"
        elif num == cls.R_ID_REJECTED:
            return "IDENTIFIER REJECTED"
        elif num == cls.R_SERVER_UNAVAILABLE:
            return "SERVER UNAVAILABLE"
        elif num == cls.R_BAD_NAME_PASS:
            return "BAD USER NAME OR PASSWORD"
        elif num == cls.R_NOT_AUTHORIZED:
            return "NOT AUTHORIZED"
        else:
            return "WARNNING: undefined code"
