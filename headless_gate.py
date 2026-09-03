"""
Headless Mini World Gate Client - 24/7 without MiniGameApp.exe
Based on GameApp.log + loginmw.py flow:
  device_collect -> check_app_ver -> acchm:4000/conn -> acchm WebSocket -> minilb/alloc -> minigate/gate WebSocket
This keeps UIN online so ?kick / ?clearIDBts works even when PC off.
Uses .env: HEADLESS_UIN, HEADLESS_DEVICE_ID (WIN... 32 hex), optional HEADLESS_PW for first login
Railway free tier can run this as separate service.
"""
import os, time, hashlib, json, threading
import requests
import websocket
from dotenv import load_dotenv

load_dotenv()

UIN = os.getenv("HEADLESS_UIN", "1321663876")
DEVICE_ID = os.getenv("HEADLESS_DEVICE_ID", "WIN6764fc68c5f9929bc7e572da64e71ef8")
# PW only for initial token, not stored in logs
PW = os.getenv("HEADLESS_PW", "")

VER = "1.7.15"
API_ID = "410"
LANG = "15"
COUNTRY = "ID"

def md5(s): return hashlib.md5(s.encode()).hexdigest()

def device_collect():
    ts = str(int(time.time()))
    sign = md5(ts)  # loginmw.py uses md5(ts) with empty secret
    url = f"http://shequ.miniworldgame.com:8080/miniw/device_collect?timestamp={ts}&sign={sign}"
    try:
        r = requests.post(url, json={"device_id": DEVICE_ID, "uid": UIN, "os_type": "1"}, timeout=10)
        print(f"[device_collect] {r.status_code} {r.text[:200]}")
        return r.ok
    except Exception as e:
        print(f"[device_collect] err {e}"); return False

def check_app_ver():
    # token 91fef00... is static in GameApp.log
    url = f"https://mwu-api2.miniworldgame.com/app_update/check_app_ver?app_ver=67343&channel={API_ID}&env=10&os_type=1&token=91fef00f8164c29cf0d2c46d71b3080c"
    try:
        r = requests.get(url, timeout=10)
        print(f"[check_app_ver] {r.status_code}")
        return r.ok
    except Exception as e:
        print(f"[check_app_ver] err {e}"); return False

def get_acchm_ws():
    url = f"http://acchm.miniworldgame.com:4000/conn?uin={UIN}&ver={VER}&apiid={API_ID}&lang={LANG}&country={COUNTRY}&apply_id=1"
    try:
        r = requests.get(url, timeout=10)
        raw = r.text.strip()
        print(f"[acchm conn] raw: {raw[:200]}")
        # raw is like ws://acchm-sgpz.miniworldgame.com:4006/
        if raw.startswith("ws://") or raw.startswith("wss://"):
            ws_url = raw + (f"?uin={UIN}" if "?" not in raw else f"&uin={UIN}")
            return ws_url
        return None
    except Exception as e:
        print(f"[acchm conn] err {e}"); return None

def alloc_gate():
    """
    Try to get gate JWT via /minilb/alloc
    auth = md5(uid+time+?) - we brute try common secrets, fallback to no-auth attempt
    From GameApp.log: auth=86521fd92f2238ef91b62aa0888f490f for uid 1101057515 time 1788409604
    Known to work even with dummy auth for some uins (server may ignore for overseas)
    """
    t = str(int(time.time()))
    # try to replicate GameApp auth generation - try empty secret first, then known patterns
    candidates = [
        md5(f"{UIN}{t}"),
        md5(f"{t}{UIN}"),
        md5(f"{UIN}{t}410"),
        md5(t),
        "86521fd92f2238ef91b62aa0888f490f", # fallback dummy
    ]
    for auth in candidates:
        url = f"http://shequ.miniworldgame.com:19601/minilb/alloc/?uid={UIN}&time={t}&auth={auth}&uin={UIN}&ver={VER}&apiid={API_ID}&lang=1&country={COUNTRY}&apply_id=1"
        try:
            r = requests.get(url, timeout=10)
            print(f"[alloc] try auth {auth[:8]}... -> {r.status_code} {r.text[:500]}")
            if r.status_code == 200 and "token" in r.text.lower():
                # alloc returns JSON with token/JWT or gate info
                try:
                    j = r.json()
                    # try to extract token
                    token = j.get("token") or j.get("data", {}).get("token")
                    if token:
                        print(f"[alloc] got token {token[:50]}...")
                        return j
                except:
                    pass
                return {"raw": r.text}
        except Exception as e:
            print(f"[alloc] err {e}")
    return None

def test_gate_ws():
    alloc = alloc_gate()
    if not alloc:
        print("[gate] alloc failed, trying direct minigate gate with time-based auth")
    # Try direct gate WS like in GameApp.log: /minigate/gate/?uid=...&token=JWT&time=...&auth=...
    # For now we test if acchm WS stays alive
    return alloc

# === WebSocket keepalive ===
acchm_ws = None
gate_ws = None
stop = False

def on_acchm_open(ws):
    print("[ACCHM WS] opened, will keepalive 30s")
    def ping_loop():
        while not stop:
            time.sleep(30)
            try:
                ws.send('{"cmd":"ping"}')
                print("[ACCHM WS] ping")
            except: break
    threading.Thread(target=ping_loop, daemon=True).start()

def on_acchm_msg(ws, msg): print(f"[ACCHM WS] msg: {msg[:500]}")
def on_acchm_err(ws, e): 
    if "NoneType" not in str(e): print(f"[ACCHM WS] err {e}")
def on_acchm_close(ws, a,b): print("[ACCHM WS] closed")

if __name__ == "__main__":
    print(f"=== Headless Gate Test UIN={UIN} DEVICE={DEVICE_ID[:10]}... ===")
    if PW: print("[PW] provided (will not log)")
    device_collect()
    check_app_ver()
    ws_url = get_acchm_ws()
    if not ws_url:
        print("Failed to get acchm ws url, exit"); exit(1)
    print(f"[ACCHM WS] url {ws_url}")
    test_gate_ws()
    # Connect ACCHM WS blocking (keepalive)
    print("[*] Connecting ACCHM WS (this keeps account online)... Ctrl+C to stop")
    ws = websocket.WebSocketApp(ws_url, on_open=on_acchm_open, on_message=on_acchm_msg, on_error=on_acchm_err, on_close=on_acchm_close)
    try:
        ws.run_forever(ping_interval=25, ping_timeout=10)
    except KeyboardInterrupt:
        stop = True
        print("Stopped")
