"""Replay gate for 1321663876 using captured token from Gate test.pcapng - no MiniGameApp needed for 12 days"""
import websocket, time, threading

# Captured from Gate test.pcapng
GATE_URL = "ws://183.87.99.86:19702/minigate/gate/?uid=1321663876&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aW4iOiIxMzIxNjYzODc2IiwidGltZSI6MTc4ODQxNzI4MCwiZXhwIjoxNzg5NjI2ODgwLCJpc3MiOiJpbXNlcnZlciJ9.xQ8KsHZZW3aLKkCxjcGwSc-heJukhBlOFHfKqkH_KqA&time=1788417277&auth=c0e61ba4db06f8d1d82153db03812b24&cltversion=67343&apiid=410&reconnect=0"

def on_open(ws):
    print("[GATE] OPENED for 1321663876 - will keep 12 days")
    # gate heartbeat is binary, not text - just keep ws alive via library ping
    pass
def on_msg(ws, msg):
    print(f"[GATE] msg {repr(msg[:200])}")
def on_err(ws, e):
    print(f"[GATE] err {e}")
def on_close(ws, c, m):
    print(f"[GATE] close {c} {m} - will reconnect")

print("=== Replay GATE 1321663876 (captured token) - auto reconnect ===")
while True:
    ws = websocket.WebSocketApp(GATE_URL, on_open=on_open, on_message=on_msg, on_error=on_err, on_close=on_close)
    ws.run_forever(ping_interval=20, ping_timeout=10)
    print("[GATE] reconnecting in 5s...")
    time.sleep(5)
