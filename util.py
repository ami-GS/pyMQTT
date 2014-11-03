from binascii import hexlify

def upackHex(val):
    return int(hexlify(val), 16)

def packHex(val, l = 2):
    if type(val) == str and len(val) >= 2:
        return  "".join([packHex(c) for c in val])
    elif type(val) == str:
        return hex(ord(val))[2:].zfill(l)
    elif type(val) == int:
        return hex(val)[2:].zfill(l)

def utfEncode(val):
    return packHex(len(val), 4) + packHex(val)

def utfDecode(val):
    idx = upackHex(val[:2])
    content = val[2:2+idx]
    return content, idx + 2
