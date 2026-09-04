"""Handle black (block) 1320454366 via friend server - headless, no MiniGameApp, from Kick try scan.pcapng"""
import requests, time

# Captured from Kick try scan.pcapng: handle_black
url = "http://friend.miniworldgame.com:8180//server/friend"
params = {
    "apiid": "410",
    "cmd": "handle_black",
    "country": "ID",
    "des_uin": "1320454366",
    "lang": "1",
    "op_type": "1",  # 1=add black, 0=remove?
    "src_uin": "1321663876",
    "ver": "1.7.15",
    "auth": "30e0e9334da017fef8a6c8c1d9e2c0a08"  # from capture - may need fresh generation
}

print(f"Blocking {params['des_uin']} from {params['src_uin']}...")
try:
    r = requests.get(url, params=params, timeout=10)
    print(f"Status {r.status_code}")
    print(r.text[:1000])
    if "result" in r.text or "code" in r.text:
        print("Check if blocked")
except Exception as e:
    print(f"err {e}")

# Try with fresh time/auth generation (if above auth expired, try to generate new)
# The auth for handle_black is likely MD5(src_uin+des_uin+time+secret)
# For now try to reuse same auth with fresh time
import hashlib
def md5(s): return hashlib.md5(s.encode()).hexdigest()
# Try to generate new auth with current time
t = str(int(time.time()))
# try known secret
for sec in ["#_php_miniw_2016_#", ""]:
    auth_try = md5(f"{params['src_uin']}{params['des_uin']}{t}{sec}")
    print(f"try auth {auth_try} with sec {sec} time {t}")
