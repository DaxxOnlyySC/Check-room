"""Headless friend kick for 1320454366 using 2 spam accounts - no MiniGameApp needed"""
import requests, time
from concurrent.futures import ThreadPoolExecutor

des_uin = "1320454366"  # target
url = "http://friend.miniworldgame.com:8180//server/friend"

# Reuse your 2 working accounts (valid token/auth)
accounts = [
    {
        "name": "Acc 1146608460",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6Ilx1YTczMVx1MDI2YVx1MDI3NFx1MWQwMFx1MDI5Zlx1MWQwZlx1MWQwMC4iLCJzaGFyZVR5cGUiOjF9",
            "lang": "10", "msg": "kick", "s2t": "1750817736",
            "src_uin": "1146608460", "time": "1750819175",
            "token": "644ee6cc06f4c7c7f4ed5f4cb355f27d", "uin": "1146608460",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "6ba18235c5b6a5bd1bcc25b89205d97a",
            "mmsum": "65004861af99a61750819111", "cthash": "9d5ac80a1a"
        }
    },
    {
        "name": "Acc 1308620729",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6IlTDrG0gTWVvIEto4bqvcCBTZXZlciIsInNoYXJlVHlwZSI6MH0%5F",
            "lang": "10", "msg": "kick", "s2t": "1750829644",
            "src_uin": "1308620729", "time": "1750829702",
            "token": "bc995ad82c46529357a94536294f5bf9", "uin": "1308620729",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "0bec97b74bbe04ce4be432409a4475a5",
            "mmsum": "5400fab98b416c1750829647", "cthash": "6449db67d3"
        }
    },
]

def send_one(acc):
    try:
        r = requests.get(url, params=acc["params"], timeout=10)
        return f"{acc['name']} {r.status_code} {r.text[:100]}"
    except Exception as e:
        return f"{acc['name']} err {e}"

print(f"=== Headless friend kick {des_uin} - loop every 5s (no MiniGameApp) ===")
while True:
    with ThreadPoolExecutor(max_workers=2) as ex:
        for res in ex.map(send_one, accounts):
            print(res)
    print("--- sleep 5s ---")
    time.sleep(5)
