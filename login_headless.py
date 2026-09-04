"""Login headless with UIN+PW to generate s2t/token/auth - test"""
import os, time, hashlib, requests
from dotenv import load_dotenv
load_dotenv()

UIN = os.getenv("HEADLESS_UIN", "1321663876")
PW = os.getenv("HEADLESS_PW", "TheDark12345#")  # will not be logged
DEVICE_ID = os.getenv("HEADLESS_DEVICE_ID", "WIN6764fc68c5f9929bc7e572da64e71ef8")

def md5(s): return hashlib.md5(s.encode()).hexdigest()

# 1. device_collect
ts = str(int(time.time()))
sign = md5(ts)
print(f"[1] device_collect ts={ts} sign={sign}")
try:
    r = requests.post(f"http://shequ.miniworldgame.com:8080/miniw/device_collect?timestamp={ts}&sign={sign}", json={"device_id": DEVICE_ID, "uid": UIN, "os_type": "1"}, timeout=10)
    print(f" -> {r.status_code} {r.text[:300]}")
except Exception as e:
    print(f"err {e}")

# 2. Try to generate s2t/token/auth like getUrlAuth
s2t = str(int(time.time()))
# Try to mimic libiworld getUrlAuth: s2t is current time, token = md5(s2t+secret) ?
# We try with known secret
secret = "#_php_miniw_2016_#"
token_try = md5(s2t + UIN + secret)
print(f"[2] s2t={s2t} try token MD5(s2t+uin+secret) = {token_try}")

# 3. Try login via shequ with s7 (need to generate s7) - try simple
# For now just try to get conn url (which works without PW)
try:
    r = requests.get(f"http://acchm.miniworldgame.com:4000/conn?uin={UIN}&ver=1.7.15&apiid=410&lang=15&country=ID&apply_id=1", timeout=10)
    print(f"[3] acchm conn: {r.text[:200]}")
except Exception as e:
    print(f"err {e}")

print(f"[PW] provided len={len(PW)} (not logged) - if login needs PW, it would be hashed via s7")
