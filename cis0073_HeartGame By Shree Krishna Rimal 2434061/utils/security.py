import hashlib,hmac,os,base64
from config import SECRET_KEY

def hash_password(password,salt=None):
    if salt is None: salt=os.urandom(16)
    dk=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,100000)
    return base64.b64encode(salt).decode(),base64.b64encode(dk).decode()

def verify_password(password,b64salt,b64hash):
    salt=base64.b64decode(b64salt.encode())
    dk=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,100000)
    return hmac.compare_digest(base64.b64encode(dk).decode(),b64hash)

def sign_value(v):
    mac=hmac.new(SECRET_KEY.encode(),msg=v.encode(),digestmod='sha256').digest()
    return base64.urlsafe_b64encode(mac).decode()

def encode_session(uid,uname,is_admin):
    payload=f"{uid}|{uname}|{is_admin}"
    sig=sign_value(payload)
    return f"{payload}|{sig}"

def decode_session(tok):
    try:
        uid,uname,is_admin,sig=tok.split('|')
        exp=sign_value(f"{uid}|{uname}|{is_admin}")
        if hmac.compare_digest(sig,exp):
            return int(uid),uname,int(is_admin)
    except Exception:
        pass
    return None
