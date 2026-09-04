"""Combined kick: gm.kick via gate + handle_black via friend - try both for 1320454366"""
import websocket, requests, time, threading

GATE_URL = "ws://183.87.99.86:19702/minigate/gate/?uid=1321663876&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aW4iOiIxMzIxNjYzODc2IiwidGltZSI6MTc4ODQxNzI4MCwiZXhwIjoxNzg5NjI2ODgwLCJpc3MiOiJpbXNlcnZlciJ9.xQ8KsHZZW3aLKkCxjcGwSc-heJukhBlOFHfKqkH_KqA&time=1788417277&auth=c0e61ba4db06f8d1d82153db03812b24&cltversion=67343&apiid=410&reconnect=0"
TARGET = "1320454366"
FRIEND_URL = "http://friend.miniworldgame.com:8180//server/friend"

def gate_kick():
    def on_open(ws):
        print(f"[GATE] OPENED - gm.kick {TARGET}")
        def loop():
            while True:
                time.sleep(10)
                try:
                    ws.send(f"AccountManager.cluster.buddysvr.routemore('gm.kick','{TARGET}',0)")
                    print(f"[GATE] gm.kick {TARGET}")
                    ws.send(f"AccountManager.cluster.buddysvr.routemore('data.capture','{TARGET}',54188)")
                    print(f"[GATE] data.capture {TARGET}")
                except: break
        threading.Thread(target=loop, daemon=True).start()
    ws = websocket.WebSocketApp(GATE_URL, on_open=on_open, on_message=lambda w,m: print(f"[GATE] msg {m[:100]}"), on_error=lambda w,e: print(e), on_close=lambda w,c,m: print(f"close {c}"))
    ws.run_forever(ping_interval=20)

def friend_kick():
    params = {"apiid":"410","cmd":"handle_black","country":"ID","des_uin":TARGET,"lang":"1","op_type":"1","src_uin":"1321663876","ver":"1.7.15","auth":"30e0e9334da017fef8a6c8c1d9e2c0a08"}
    while True:
        try:
            r = requests.get(FRIEND_URL, params=params, timeout=10)
            print(f"[FRIEND] handle_black {r.text[:100]}")
        except Exception as e:
            print(f"[FRIEND] err {e}")
        time.sleep(15)

print("=== Combined kick 1320454366 - gate + friend ===")
threading.Thread(target=gate_kick, daemon=True).start()
friend_kick()
