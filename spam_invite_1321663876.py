"""Spam invite/chat to 129008846 using 7 working accounts + 1321663876 (headless, no MiniGameApp)"""
import requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed

des_uin = "129008846"  # target invite - will be auto padded to 10129008846? keep as is for friend API
url = "http://friend.miniworldgame.com:8180//server/friend"
TOTAL_REQUESTS = 100  # reduced for invite spam
MAX_WORKERS = 20

messages = [
    "INVITE INVITE INVITE JOIN ROOM Back to School 2.0",
    "Join my room 1321663876 - Back to School",
]

# 7 working accounts from your script (valid token/auth)
accounts = [
    {
        "name": "Acc 1146608460",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6Ilx1YTczMVx1MDI2YVx1MDI3NFx1MWQwMFx1MDI5Zlx1MWQwZlx1MWQwMC4iLCJzaGFyZVR5cGUiOjF9",
            "lang": "10", "msg": messages[0], "s2t": "1750817736",
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
            "lang": "10", "msg": messages[0], "s2t": "1750829644",
            "src_uin": "1308620729", "time": "1750829702",
            "token": "bc995ad82c46529357a94536294f5bf9", "uin": "1308620729",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "0bec97b74bbe04ce4be432409a4475a5",
            "mmsum": "5400fab98b416c1750829647", "cthash": "6449db67d3"
        }
    },
    {
        "name": "Acc 1192548629",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6ImfDoCEhIiwic2hhcmVUeXBlIjowfQ%5F%5F",
            "lang": "10", "msg": messages[0], "s2t": "1750829916",
            "src_uin": "1192548629", "time": "1750829934",
            "token": "1d4b28d4a358d02b1ce6f06ad909728c", "uin": "1192548629",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "3666899d8b4ad908986bd8b88165bcd3",
            "mmsum": "1800cb7449aa721750829916", "cthash": "cc204b64ee"
        }
    },
    {
        "name": "Acc 1312056825",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6IkFwaV8zIiwic2hhcmVUeXBlIjowfQ__",
            "lang": "10", "msg": messages[1], "s2t": "1750928975",
            "src_uin": "1312056825", "time": "1750929004",
            "token": "d44c9e41c9b7f684ff4da1077790ae5a", "uin": "1312056825",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "3fd0b0431213250c7918432fd96a432e",
            "mmsum": "2800aea34a81be1750928976", "cthash": "8f26e57899"
        }
    },
    {
        "name": "Acc 1312056657",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6IkFwaV8xIiwic2hhcmVUeXBlIjowfQ__",
            "lang": "10", "msg": messages[1], "s2t": "1750929041",
            "src_uin": "1312056657", "time": "1750929091",
            "token": "94f04f014e97c183a8fa9d3c0e8e8607", "uin": "1312056657",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "7f277fdb51c8e528ac317f6e1803788a",
            "mmsum": "50001671fc28c31750929041", "cthash": "36d7c00070"
        }
    },
    {
        "name": "Acc 1312056847",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6IkFwaV8yIiwic2hhcmVUeXBlIjowfQ__",
            "lang": "10", "msg": messages[1], "s2t": "1750929115",
            "src_uin": "1312056847", "time": "1750929138",
            "token": "e6382f16c2ea4ad07720f578a5087bd1", "uin": "1312056847",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "3174c0fc73006e897c217ca15ac55d08",
            "mmsum": "2400f2e9b4227c1750929115", "cthash": "07c9285ec0"
        }
    },
    {
        "name": "Acc 1312056949",
        "params": {
            "apiid": "410", "cmd": "send_chat_msg", "country": "VN",
            "des_uin": des_uin, "extend_data": "eyJuaWNrbmFtZSI6IkFwaV80Iiwic2hhcmVUeXBlIjowfQ__",
            "lang": "10", "msg": messages[1], "s2t": "1750929166",
            "src_uin": "1312056949", "time": "1750929220",
            "token": "a5872fc21505e59905f4e94f3b0d3739", "uin": "1312056949",
            "ver": "1.7.15", "msgtype": "1", "pushchannel": "1",
            "auth": "0e479290c2cda0808004a3c0793db495",
            "mmsum": "5400e9ee5e03441750929166", "cthash": "b2f67a4c60"
        }
    },
    # Add your 1321663876 here once you capture its friend token (optional)
]

def send_message(acc_name, acc_params, i):
    try:
        r = requests.get(url, params=acc_params, timeout=5)
        if r.status_code == 200:
            print(f"[{acc_name} | {i+1}] {r.text[:120]}")
        else:
            print(f"[{acc_name} | {i+1}] {r.status_code}")
    except Exception as e:
        print(f"[{acc_name} | {i+1}] err {e}")

print(f"=== Spam invite to {des_uin} using 7 acc ===")
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures = []
    for acc in accounts:
        for i in range(TOTAL_REQUESTS):
            futures.append(ex.submit(send_message, acc["name"], acc["params"], i))
    for f in as_completed(futures):
        pass
print("Done")
