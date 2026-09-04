import requests, time, urllib.parse

# Captured from ROom.pcapng for 1321663876
base_url = "http://openroom-inaz.miniworldgame.com:8080/server/room"

params = {
    "can_trace": "1",
    "cmd": "create_room",
    "connect_mode": "0",
    "country": "ID",
    "desc": "",
    "device": "410",
    "extra_data": '{"audioconfigurl":"http://ak-hwmap3.miniworldgame.com/map/3/time20260904/e2fa91f3cff0657c4ba45aae1d88087b","autoTag":"Circuit","editorSceneSwitch":0,"gender":0,"limit":6,"map_version":1781071464,"modUuids":[],"modurl":"http://ak-hwmap3.miniworldgame.com/map/3/plugin20260904/73b6059522c7f186c9bd12643c709e13","platform":1,"translate":"","translate_sourcelang":1,"translate_supportlang":65279,"uilibsurl":"http://ak-hwmap3.miniworldgame.com/map/3/plugin20260904/89a3271b3e2264ab9f9df9a043560459","uniqueCode":"001321663876001788493412b8ad3af0b2f4072c323f7e57bbbd5aaf","version":"1.7.15","vipExp":0,"vipLevel":0,"vipType":0}',
    "frame": "0",
    "game_label": "5",
    "has_avatar": "1",
    "map_id": "823355e702b39b643e0310f9b30e2873",
    "map_name": "Back To School [2.0]",
    "map_type": "41834052663740",
    "map_version": "1781071464",
    "max_count": "40",
    "net_area": "0",
    "net_isp": "0",
    "net_status": "2",
    "passwd": "",
    "proxy_connected": "0",
    "proxy_ip": "164.52.72.108",
    "proxy_port": "51005",
    "punch_ip": "164.52.28.134",
    "punch_port": "60025",
    "right": "1",
    "room_name": "Back To School [2.0]",
    "room_type": "5",
    "s2t": str(int(time.time())),
    "thumbnail": "",
    "time": str(int(time.time())),
    "token": "99e4f17ce52faaaaccc7dffecdb10c42",
    "uicon": "2",
    "uicon_box": "1",
    "uin": "1321663876",
    "uname": "#BDaxterr!",
    "use_proxy": "0",
    "version": "1.7.15",
    "public_type": "0",
    "prei_room_name_idx": "0",
    "regapiid": "0",
}

print(f"Creating room for {params['uin']} {params['map_name']}...")
try:
    r = requests.get(base_url, params=params, timeout=10)
    print(f"Status {r.status_code}")
    print(r.text[:2000])
    if "room" in r.text.lower() or "code" in r.text.lower():
        print("Check response for room creation")
except Exception as e:
    print(f"err {e}")
