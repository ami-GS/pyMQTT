from binascii import hexlify

def upackHex(val):
    return int(hexlify(val), 16)
