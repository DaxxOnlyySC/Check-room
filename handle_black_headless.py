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

# Try with fresh time/auth generation
import hashlib
def md5(s): return hashlib.md5(s.encode()).hexdigest()
t = str(int(time.time()))
for sec in ["#_php_miniw_2016_#", ""]:
    auth_try = md5(f"{params['src_uin']}{params['des_uin']}{t}{sec}")
    print(f"try auth {auth_try} with sec {sec} time {t}")
    p2 = params.copy()
    p2["auth"] = auth_try
    p2["time"] = t  # some APIs need time param, but handle_black uses auth only? try anyway
    try:
        r2 = requests.get(url, params=p2, timeout=10)
        print(f" -> fresh {r2.status_code} {r2.text[:500]}")
    except Exception as e:
        print(f"err {e}")

# Also try op_type=0 to unblack then re-black (if result 2 = already black)
print("Try unblack then re-black...")
for op in ["0", "1"]:
    p3 = params.copy()
    p3["op_type"] = op
    p3["auth"] = "30e0e9334da017fef8a6c8c1d9e2c0a08"  # original
    try:
        r3 = requests.get(url, params=p3, timeout=10)
        print(f"op_type={op} -> {r3.text[:300]}")
    except Exception as e:
        print(e)
