import hashlib


def getUserId(userInfo):
    userSub = userInfo["sub"]
    res = hashlib.md5(userSub.encode('utf-8')).hexdigest()
    return res
