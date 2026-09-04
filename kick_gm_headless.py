"""Python version of Lua gm.kick for 1321403793 - headless via gate (no MiniGameApp)"""
import websocket, time, threading

GATE_URL = "ws://183.87.99.86:19702/minigate/gate/?uid=1321663876&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aW4iOiIxMzIxNjYzODc2IiwidGltZSI6MTc4ODQxNzI4MCwiZXhwIjoxNzg5NjI2ODgwLCJpc3MiOiJpbXNlcnZlciJ9.xQ8KsHZZW3aLKkCxjcGwSc-heJukhBlOFHfKqkH_KqA&time=1788417277&auth=c0e61ba4db06f8d1d82153db03812b24&cltversion=67343&apiid=410&reconnect=0"
TARGET = "1321403793"

def on_open(ws):
    print(f"[GATE] OPENED - kick {TARGET} via gm.kick")
    def kick_loop():
        while True:
            time.sleep(0.1)
            try:
                # Lua: AccountManager.cluster.buddysvr.routemore('gm.kick', targetUin, 0)
                # Headless: send same via gate as text (will be converted to binary by server)
                payload = f'gm.kick:{TARGET}:0'
                ws.send(payload)
                print(f"[KICK] sent gm.kick {TARGET}")
                # also try Lua format for compatibility
                lua = f"AccountManager.cluster.buddysvr.routemore('gm.kick', '{TARGET}', 0)"
                ws.send(lua)
                time.sleep(5)
            except Exception as e:
                print(f"kick err {e}")
                break
    threading.Thread(target=kick_loop, daemon=True).start()

def on_msg(ws, m): print(f"[GATE] msg {repr(m[:200])}")
def on_err(ws, e): print(f"[GATE] err {e}")
def on_close(ws, c, m): print(f"[GATE] close {c} {m}")

print(f"=== Headless GM Kick {TARGET} (from Lua DARKN2ss) ===")
while True:
    ws = websocket.WebSocketApp(GATE_URL, on_open=on_open, on_message=on_msg, on_error=on_err, on_close=on_close)
    ws.run_forever(ping_interval=20, ping_timeout=10)
    print("reconnect 5s...")
    time.sleep(5)
