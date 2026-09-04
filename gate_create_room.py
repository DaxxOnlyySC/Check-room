"""Gate keepalive + create Back to School room for 1321663876 - combined headless"""
import websocket, time, threading, requests

GATE_URL = "ws://183.87.99.86:19702/minigate/gate/?uid=1321663876&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aW4iOiIxMzIxNjYzODc2IiwidGltZSI6MTc4ODQxNzI4MCwiZXhwIjoxNzg5NjI2ODgwLCJpc3MiOiJpbXNlcnZlciJ9.xQ8KsHZZW3aLKkCxjcGwSc-heJukhBlOFHfKqkH_KqA&time=1788417277&auth=c0e61ba4db06f8d1d82153db03812b24&cltversion=67343&apiid=410&reconnect=0"
ROOM_URL = "http://openroom-inaz.miniworldgame.com:8080/server/room"

def on_open(ws):
    print("[GATE] OPENED - will create room in 3s")
    def do_create():
        time.sleep(3)
        params = {
            "can_trace": "1","cmd": "create_room","connect_mode": "0","country": "ID","desc": "","device": "410",
            "extra_data": '{"audioconfigurl":"http://ak-hwmap3.miniworldgame.com/map/3/time20260904/e2fa91f3cff0657c4ba45aae1d88087b","autoTag":"Circuit","editorSceneSwitch":0,"gender":0,"limit":6,"map_version":1781071464,"modUuids":[],"modurl":"http://ak-hwmap3.miniworldgame.com/map/3/plugin20260904/73b6059522c7f186c9bd12643c709e13","platform":1,"translate":"","translate_sourcelang":1,"translate_supportlang":65279,"uilibsurl":"http://ak-hwmap3.miniworldgame.com/map/3/plugin20260904/89a3271b3e2264ab9f9df9a043560459","uniqueCode":"001321663876001788493412b8ad3af0b2f4072c323f7e57bbbd5aaf","version":"1.7.15","vipExp":0,"vipLevel":0,"vipType":0}',
            "frame": "0","game_label": "5","has_avatar": "1","map_id": "823355e702b39b643e0310f9b30e2873","map_name": "Back To School [2.0]","map_type": "41834052663740","map_version": "1781071464","max_count": "40","net_area": "0","net_isp": "0","net_status": "2","passwd": "","proxy_connected": "0","proxy_ip": "164.52.72.108","proxy_port": "51005","punch_ip": "164.52.28.134","punch_port": "60025","right": "1","room_name": "Back To School [2.0]","room_type": "5","s2t": "1788493378","thumbnail": "","time": "1788493413","token": "99e4f17ce52faaaaccc7dffecdb10c42","uicon": "2","uicon_box": "1","uin": "1321663876","uname": "#BDaxterr!","use_proxy": "0","version": "1.7.15","public_type": "0","prei_room_name_idx": "0","regapiid": "0",
        }
        try:
            r = requests.get(ROOM_URL, params=params, timeout=10)
            print(f"[ROOM] create {r.status_code} {r.text[:500]}")
        except Exception as e:
            print(f"[ROOM] err {e}")
    threading.Thread(target=do_create, daemon=True).start()

def on_msg(ws, m): print(f"[GATE] msg {repr(m[:100])}")
def on_err(ws, e): print(f"[GATE] err {e}")
def on_close(ws, c, m): print(f"[GATE] close {c} {m}")

print("=== Gate + Create Room 1321663876 ===")
while True:
    ws = websocket.WebSocketApp(GATE_URL, on_open=on_open, on_message=on_msg, on_error=on_err, on_close=on_close)
    ws.run_forever(ping_interval=20, ping_timeout=10)
    print("reconnect 5s...")
    time.sleep(5)
