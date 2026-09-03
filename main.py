import sys, os, time, requests, re, random, string, asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import discord
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX", "?")

if not TOKEN:
    print("[!] DISCORD_TOKEN not found in .env!")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))
BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:18234")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "mwbot_secret_2024")

ACTIVE_BANS = {}
REPORT_STATS = {"total": 0, "banned": 0, "reporters": set()}


def fix_uin(uin):
    s = str(uin).strip()
    if len(s) == 8:
        s = "10" + s
    elif len(s) == 9:
        s = "1" + s
    return s


# ============== BRIDGE / KICK ==============

async def send_lua_via_bridge(code):
    try:
        r = await asyncio.to_thread(
            lambda: requests.post(
                f"{BRIDGE_URL}/exec",
                json={"action": "exec", "code": code},
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "ngrok-skip-browser-warning": "true",
                },
                timeout=10,
            )
        )
        return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


async def inject_dll():
    try:
        r = await asyncio.to_thread(
            lambda: requests.post(
                f"{BRIDGE_URL}/exec",
                json={"action": "inject"},
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "ngrok-skip-browser-warning": "true",
                },
                timeout=15,
            )
        )
        return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


OWNER_ID = 1286240448775720962


KICK_LUA = '''\
local targetUin = "{uin}"

local ok, err = pcall(function()
    AccountManager.cluster.buddysvr.routemore('data.capture', targetUin, 54188)
end)

if ok then
    if ShowGameTipsWithoutFilter then
        ShowGameTipsWithoutFilter("#cff0000Target blocked: " .. targetUin)
    end
    return "Blocked screen: " .. targetUin
else
    return "Error: " .. tostring(err)
end
'''


NOTIF_LUA = '''\
local targetUin = "{uin}"
local notifText = "{text}"

local ok, err = pcall(function()
    AccountManager:routemore("teamservice.notifyMember", targetUin, {{
        Text = notifText,
        Type = "NotifyTips",
        ExceptIds = 1000
    }})
end)

if ok then
    return "Notification sent to " .. targetUin
else
    return "Error: " .. tostring(err)
end
'''


# ============== HELPERS ==============

def fix_uin(uin):
    s = str(uin).strip()
    if len(s) == 8:
        s = "10" + s
    elif len(s) == 9:
        s = "1" + s
    return s


# ============== API ==============

def fetch_maps(uin):
    uin_str = fix_uin(uin)
    t = int(time.time())
    url = (
        f"http://shequ.miniworldgame.com:8080/miniw/map/"
        f"?act=get_room_new_tab_oversea"
        f"&uin={uin_str}&country=ID&apiid=410"
        f"&s2t={t}&ver=1.7.15&time={t}"
        f"&section=INA&requestid=12345&lang=15&refreshIndex=1"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return parse_maps(r.text), uin_str
        return {"error": f"HTTP {r.status_code}"}, uin_str
    except Exception as e:
        return {"error": str(e)}, uin_str


def parse_maps(raw):
    result = []
    for block in re.split(r'\[\d+\]=\{', raw)[1:]:
        try:
            wid = re.search(r'\["wid"\]="?(\d+)"?', block)
            name = re.search(r'\["name"\]="([^"]*)"', block)
            play = re.search(r'\["play_count"\]=(\d+)', block)
            collect = re.search(r'\["collectc"\]=(\d+)', block)
            if wid:
                result.append({
                    "wid": wid.group(1),
                    "name": name.group(1) if name else "Unnamed",
                    "plays": int(play.group(1)) if play else 0,
                    "favs": int(collect.group(1)) if collect else 0,
                })
        except:
            continue
    return result


def fetch_sign_status(uin):
    uin_str = fix_uin(uin)
    t = int(time.time())
    url = (
        f"http://shequ.miniworldgame.com:8080/miniw/mission"
        f"?act=hw_daily_sign_status"
        f"&timezone=420&uin={uin_str}&headInd=2"
        f"&apiid=410&s2t={t}&ver=1.7.15&time={t}"
        f"&md5=test&country=ID&lang=15"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return parse_sign(r.text), uin_str
        return {"error": f"HTTP {r.status_code}"}, uin_str
    except Exception as e:
        return {"error": str(e)}, uin_str


def parse_sign(raw):
    result = {}
    try:
        m = re.search(r'\["ret"\]=(\d+)', raw)
        if m: result["ret"] = int(m.group(1))
        m = re.search(r'\["signCount"\]=(\d+)', raw)
        if m: result["signCount"] = int(m.group(1))
        m = re.search(r'\["signTime"\]=(\d+)', raw)
        if m:
            ts = int(m.group(1))
            result["signTime"] = datetime.fromtimestamp(ts + 7 * 3600).strftime("%d %b %Y, %H:%M WIB")
        m = re.search(r'\["timeZone"\]=(\d+)', raw)
        if m: result["timeZone"] = int(m.group(1))
        m = re.search(r'\["signRecord"\]=\{(.+?)\}', raw)
        if m:
            days = re.findall(r'\[(\d+)\]=(\d+)', m.group(1))
            result["signRecord"] = {int(d): int(v) for d, v in days}
    except:
        pass
    return result


# ============== ROOM ==============

def read_bak_profile(uin):
    cache_dir = os.path.expanduser(r"~\AppData\Roaming\miniworddata410\data\account\http___hwacchm.mini1.cn_4000")
    if not os.path.exists(cache_dir):
        return None
    targets = [uin, f"1{uin}", f"10{uin}", f"11{uin}"]
    for f in os.listdir(cache_dir):
        if not f.endswith(".data2tmp.bak"):
            continue
        for t in targets:
            if t in f:
                fp = os.path.join(cache_dir, f)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    return parse_bak_profile(content)
                except:
                    pass
    return None


def parse_bak_profile(content):
    data = {}
    m = re.search(r'NickName\s*=\s*\[\[([^\]]+)\]\]', content)
    if m: data['NickName'] = m.group(1)
    m = re.search(r'Country\s*=\s*\[\[([^\]]+)\]\]', content)
    if m: data['Country'] = m.group(1).upper()
    m = re.search(r'Gender\s*=\s*(\d+)', content)
    if m:
        g = m.group(1)
        data['Gender'] = "Male" if g == "1" else ("Female" if g == "2" else "Hidden")
    m = re.search(r'Popularity\s*=\s*(\d+)', content)
    if m: data['Popularity'] = m.group(1)
    m = re.search(r'MoodText\s*=\s*\[\[([^\]]*)\]\]', content)
    if m and m.group(1).strip(): data['Bio'] = m.group(1).strip()
    m = re.search(r'HeadFrameID\s*=\s*(\d+)', content)
    if m and int(m.group(1)) > 0: data['Frame'] = m.group(1)
    m = re.search(r'DeviceID\s*=\s*\[\[([^\]]+)\]\]', content)
    if m: data['DeviceID'] = m.group(1)
    m = re.search(r'Email\s*=\s*\[\[([^\]]*)\]\]', content)
    if m and m.group(1).strip(): data['Email'] = m.group(1)
    m = re.search(r'MiniBean\s*=\s*(\d+)', content)
    if m: data['MiniBean'] = m.group(1)
    m = re.search(r'MiniCoin\s*=\s*(\d+)', content)
    if m: data['MiniCoin'] = m.group(1)
    m = re.search(r'Diamond\s*=\s*(\d+)', content)
    if m: data['Diamond'] = m.group(1)
    m = re.search(r'AccountCreateTime\s*=\s*(\d+)', content)
    if m: data['CreateDate'] = datetime.fromtimestamp(int(m.group(1))).strftime('%d/%m/%Y')
    m = re.search(r'LastLoginTime\s*=\s*(\d+)', content)
    if m: data['LastLogin'] = datetime.fromtimestamp(int(m.group(1))).strftime('%d/%m/%Y %H:%M')
    m = re.search(r'FriendAttention\s*=\s*(\d+)', content)
    if m: data['Following'] = m.group(1)
    m = re.search(r'FriendBeattention\s*=\s*(\d+)', content)
    if m: data['Followers'] = m.group(1)
    m = re.search(r'FriendEachother\s*=\s*(\d+)', content)
    if m: data['Friends'] = m.group(1)
    return data if data else None


def fetch_items(uin):
    uin_str = fix_uin(uin)
    url = f"http://update.miniworldgame.com:6000/miscquery/query_avatar_list_by_uin/?uin={uin_str}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("msg"):
                items = data["msg"]
                total = len(items)
                perm = sum(1 for i in items if i.get("ExpireTime") == -1)
                temp = total - perm
                by_part = {}
                for i in items:
                    p = i.get("Part", 0)
                    if p not in by_part:
                        by_part[p] = {"perm": 0, "temp": 0}
                    if i.get("ExpireTime") == -1:
                        by_part[p]["perm"] += 1
                    else:
                        by_part[p]["temp"] += 1
                return {"total": total, "perm": perm, "temp": temp, "by_part": by_part}, None
            return None, "No data"
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


PART_NAMES = {
    1: "Hair", 2: "Face", 3: "Upper Body", 4: "Lower Body",
    5: "Wing/Back", 6: "Foot/Effect", 7: "Back Accessory",
    8: "Effect/Mount", 9: "Pet/Companion",
}


def fetch_profile(uin):
    uin_str = fix_uin(uin)
    bak_profile = read_bak_profile(uin_str)
    items_data, items_err = fetch_items(uin_str)
    return {
        "uin": uin_str,
        "profile": bak_profile,
        "items": items_data,
        "items_err": items_err,
    }, None


ROOM_APIS = {
    "back_to_school": {
        "name": "Back To School [2.0]",
        "map_id": "41834052663740",
        "url": "https://miniworld-api.daxtercarl1202.workers.dev/",
    },
    "bunny_vs_misra": {
        "name": "Bunny Vs Misra",
        "map_id": "71722766825339",
        "url": "https://miniworld-roomcloud.daxtercarl1202.workers.dev/",
    },
}


def fetch_room(key="back_to_school"):
    api = ROOM_APIS.get(key)
    if not api:
        return {"error": f"Unknown map: {key}"}
    try:
        r = requests.get(api["url"], timeout=10)
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def parse_room(data):
    if "error" in data:
        return None, data["error"]
    rooms = data.get("roomlist", [])
    if not isinstance(rooms, list):
        rooms = []
    if not rooms:
        rooms = data.get("rent", [])
        if not isinstance(rooms, list):
            rooms = []
    return {"total": len(rooms), "rooms": rooms}, None


def fetch_mapcount(map_id):
    url = (
        f"http://openroom-vnz.miniworldgame.com:8080/server/room"
        f"?channel=410&cmd=query_map_player_count"
        f"&country=ID&language=1&map_ids={map_id}"
        f"&time=1786933514&auth=9695fa2edb7aa5df53419e998aa1c867"
        f"&ver=1.7.15"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json(), None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def fetch_recent_maps(uin):
    uin_str = fix_uin(uin)
    t = int(time.time())
    url = (
        f"http://shequ.miniworldgame.com:8080/miniw/map/"
        f"?act=notify_recent_map_oversea"
        f"&uin={uin_str}&country=ID&apiid=410"
        f"&s2t={t}&ver=1.7.15&time={t}"
        f"&section=INA&requestid=12345&lang=1&wid=1"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            wids = re.findall(r'\[(\d{10,})\]=\{', r.text)
            return {"uin": uin_str, "map_ids": wids}, None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


# ============== NO-AUTH API ==============

SECTION_MAP = {
    "INA": ("INA", "ID"), "TH": ("THZ", "TH"), "THZ": ("THZ", "TH"),
    "SG": ("SGP", "SG"), "SGP": ("SGP", "SG"), "VN": ("VNZ", "VN"),
    "VNZ": ("VNZ", "VN"), "HK": ("HK", "HK"), "TW": ("TW", "TW"),
    "JP": ("JP", "JP"), "BR": ("BR", "BR"), "RU": ("RU", "RU"),
    "MY": ("MY", "MY"), "US": ("US", "US"), "ID": ("INA", "ID"),
}


def fetch_server_config(section="INA"):
    sec_info = SECTION_MAP.get(section.upper(), ("INA", "ID"))
    room_section = sec_info[0]
    country = sec_info[1]
    url = (
        f"http://openroom-{room_section.lower()}.miniworldgame.com:8080"
        f"/server/room?cmd=get_config"
        f"&uin=0&ver=1.7.15&apiid=410&lang=1&country={country}&apply_id=1"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json(), None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def fetch_query_uin(uin, section="TH"):
    uin_str = fix_uin(uin)
    sec_info = SECTION_MAP.get(section.upper(), ("THZ", "TH"))
    room_section = sec_info[0]
    url = (
        f"http://openroom-{room_section.lower()}.miniworldgame.com:8080"
        f"/server/room?cmd=query_uinindex_server"
        f"&op_uin={uin_str}&ver=1.7.15"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return {"uin": uin_str, "raw": r.text, "section": section.upper()}, None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def fetch_motion(uin):
    uin_str = fix_uin(uin)
    t = int(time.time())
    name = f"{uin_str}{t}"
    url = (
        f"http://shequ.miniworldgame.com:8080/miniw/skin/"
        f"?act=get_custom_motion_data"
        f"&name={name}&time={t}"
        f"&auth=00000000000000000000000000000000"
        f"&s2t={t}&uin={uin_str}&ver=1.7.15"
        f"&apiid=410&lang=1&country=ID&apply_id=1"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return {"uin": uin_str, "raw": r.text}, None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def parse_server_config(data):
    if not data:
        return None
    rc = data.get("room_config", {})
    sc = rc.get("server_config", {})
    result = {
        "version": rc.get("_VERSION", "N/A"),
        "latest_version": sc.get("latestVersion", "N/A"),
        "min_version": sc.get("minVersion", "N/A"),
        "max_version": sc.get("maxVersion", "N/A"),
        "block_type": sc.get("block_type", "N/A"),
        "room_name": sc.get("room_name", "N/A"),
        "area_type": sc.get("area_type", 0),
        "oversea_env": rc.get("oversea_env", False),
    }
    ms = rc.get("map_server", {})
    result["map_server"] = f"{ms.get('ip', 'N/A')}:{ms.get('port', 'N/A')}"
    rs = rc.get("room_server", {})
    result["room_server"] = f"{rs.get('ip', 'N/A')}:{rs.get('port', 'N/A')}"
    ma = rc.get("ma_server", {})
    result["ma_server"] = f"{ma.get('ip', 'N/A')}:{ma.get('port', 'N/A')}"

    cloud = rc.get("new_frame_rent_server", {})
    result["cloud_rent_url"] = cloud.get("cloud_rentUrl", "N/A")
    result["cloud_api_url"] = cloud.get("cloud_apiUrl", "N/A")
    countries = cloud.get("cloud_service_country", {})
    result["cloud_countries"] = len(countries)

    punch = rc.get("punch_server", [])
    result["punch_servers"] = len(punch)
    if punch:
        result["punch_sample"] = f"{punch[0].get('ip', 'N/A')}:{punch[0].get('port', 'N/A')} (+{len(punch)-1} more)"

    proxy = rc.get("proxy_server", [])
    result["proxy_servers"] = len(proxy)

    return result


def parse_query_uin(raw):
    ip = re.search(r'\["ip"\]="([^"]+)"', raw)
    port = re.search(r'\["port"\]=(\d+)', raw)
    result_code = re.search(r'\["result"\]=(\d+)', raw)
    return {
        "ip": ip.group(1) if ip else "N/A",
        "port": int(port.group(1)) if port else 0,
        "result": int(result_code.group(1)) if result_code else -1,
    }


# ============== WORKER PROFILE API ==============

def fetch_worker_profile(uin):
    uin_str = fix_uin(uin)
    url = f"https://profile-acc.event-miniworld.workers.dev/get={uin_str}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data, None
            return None, data.get("msg", "API error")
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def parse_worker_profile(raw_text):
    data = {}
    def extract(key, is_num=False):
        pat = re.compile(rf'\["{key}"\]\s*=\s*("([^"]*)"|([0-9\-]+))')
        m = pat.search(raw_text)
        if m:
            return m.group(2) if m.group(2) is not None else m.group(3)
        return None

    data["uin"] = extract("uin", True)
    data["nickname"] = extract("NickName")
    data["mood"] = extract("mood_text")
    data["country"] = extract("country")
    data["gender"] = "Male" if extract("gender", True) == "1" else "Female"
    data["popularity"] = extract("popularity", True)
    data["download_count"] = extract("all_download_count", True)

    # Relations
    m = re.search(r'\["relation"\]=\{(.+?)\}', raw_text)
    if m:
        rel = m.group(1)
        data["friends"] = re.search(r'\["friend_eachother"\]=(\d+)', rel)
        data["friends"] = data["friends"].group(1) if data["friends"] else "0"
        data["followers"] = re.search(r'\["friend_beattention"\]=(\d+)', rel)
        data["followers"] = data["followers"].group(1) if data["followers"] else "0"
        data["following"] = re.search(r'\["friend_attention"\]=(\d+)', rel)
        data["following"] = data["following"].group(1) if data["following"] else "0"

    # Avatar URL
    url_m = re.search(r'\["url"\]\s*=\s*"([^"]+)"', raw_text)
    data["avatar"] = url_m.group(1) if url_m else None

    # Dev level
    m = re.search(r'\["creator"\]=\{[^}]*\["level"\]=(\d+)', raw_text)
    data["dev_level"] = m.group(1) if m else None

    return data


def parse_worker_maps(raw_text):
    maps = []
    map_blocks = re.findall(r'\[(\d{10,})\]=\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', raw_text)
    for map_id, block in map_blocks:
        name = re.search(r'\["name"\]="([^"]*)"', block)
        downloads = re.search(r'\["download_count"\]=(\d+)', block)
        likes = re.search(r'\["like"\]=(\d+)', block)
        memo = re.search(r'\["memo"\]="([^"]*)"', block)
        worldtype = re.search(r'\["worldtype"\]="(\d+)"', block)
        maps.append({
            "id": map_id,
            "name": name.group(1) if name else "N/A",
            "downloads": int(downloads.group(1)) if downloads else 0,
            "likes": int(likes.group(1)) if likes else 0,
            "memo": memo.group(1) if memo else "",
            "worldtype": worldtype.group(1) if worldtype else "0",
        })
    return maps


WORLD_TYPES = {"0": "Survival", "1": "Random", "5": "Parkour/Other"}


def embed_worker_profile(data, err, real_uin=None):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)

    profile = data.get("profile", {})
    maps = data.get("maps", [])
    vip = data.get("vip", {})
    uin_display = real_uin or profile.get("uin", "N/A")

    e = discord.Embed(title=f"Profile — {profile.get('nickname', 'N/A')}", color=0xe67e22)

    if profile.get("avatar"):
        e.set_thumbnail(url=profile["avatar"])

    e.add_field(name="UID", value=uin_display, inline=True)
    e.add_field(name="Country", value=profile.get("country", "N/A"), inline=True)
    e.add_field(name="Gender", value=profile.get("gender", "N/A"), inline=True)
    e.add_field(name="Popularity", value=f"{int(profile.get('popularity', 0)):,}", inline=True)
    e.add_field(name="Download Map", value=f"{int(profile.get('download_count', 0)):,}", inline=True)
    e.add_field(name="Dev Level", value=profile.get("dev_level", "N/A"), inline=True)

    if profile.get("mood"):
        mood = profile["mood"].replace("\\n", "\n")[:200]
        e.add_field(name="Mood", value=mood, inline=False)

    e.add_field(
        name="Social",
        value=f"Friends: {profile.get('friends', '0')} | Followers: {profile.get('followers', '0')} | Following: {profile.get('following', '0')}",
        inline=False,
    )

    if vip:
        last_login = vip.get("LastLoginTime", "N/A")
        online = "Online" if vip.get("online") else "Offline"
        e.add_field(name="Status", value=online, inline=True)
        e.add_field(name="Login Terakhir", value=last_login, inline=True)

    if maps:
        desc = ""
        for i, m in enumerate(maps[:5], 1):
            wt = WORLD_TYPES.get(m["worldtype"], "Unknown")
            desc += f"**{i}.** {m['name']} (`{m['id']}`)\n"
            desc += f"    DL: {m['downloads']:,} | Like: {m['likes']:,} | {wt}\n"
        e.add_field(name=f"Map ({len(maps)} total)", value=desc, inline=False)

    e.set_footer(text=f"Via Worker API | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return e


# ============== EMBEDS ==============

def embed_map(uin, maps):
    e = discord.Embed(title=f"Map History — UIN {uin}", color=0x2ecc71)
    if not maps:
        e.description = "No map data found."
    else:
        desc = ""
        for i, m in enumerate(maps[:10], 1):
            desc += f"**{i}.** {m['name']}\n     Plays: {m['plays']:,} | Fav: {m['favs']:,}\n"
        e.description = desc
    e.set_footer(text="Mini World API")
    return e


def embed_sign(uin, data):
    if "error" in data:
        return discord.Embed(description=f"Error: {data['error']}", color=0xe74c3c)
    if data.get("ret", -1) != 0:
        return discord.Embed(description="Failed to fetch data.", color=0xe74c3c)

    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    record = data.get("signRecord", {})
    signed = sum(1 for v in record.values() if v > 0)

    e = discord.Embed(title=f"Daily Sign Status — UIN {uin}", color=0x3498db)
    e.add_field(name="Total Sign-ins", value=str(data.get("signCount", 0)), inline=True)
    e.add_field(name="Last Sign", value=data.get("signTime", "N/A"), inline=True)
    e.add_field(name="This Week", value=f"{signed}/7", inline=True)

    week = ""
    for i in range(1, 8):
        icon = "✅" if record.get(i, 0) else "❌"
        week += f"**{DAYS[i-1]}** {icon}  "
    e.description = week
    e.set_footer(text="Mini World API")
    return e


def embed_room(data, err, map_name=""):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)
    total = data.get("total", 0)
    rooms = data.get("rooms", [])

    title = f"Active Rooms — {map_name}" if map_name else "Active Rooms"
    e = discord.Embed(title=title, color=0xe74c3c)

    if not rooms:
        e.description = "No rooms found."
    else:
        header = f"```\n{'No':<4}{'Host':<16}{'UID':<12}{'Plr':<6}{'Dev':<6}{'Ping':<6}\n{'─'*50}\n```"
        rows = ""
        for i, rm in enumerate(rooms, 1):
            host = rm.get("uname", "?")[:14]
            uid = rm.get("uin", "?")
            cur = rm.get("cur_count", 0)
            mx = rm.get("max_count", 0)
            ping = rm.get("ping", "?")
            device_id = rm.get("device", "?")
            locked = "L" if rm.get("passwd") else ""
            rows += f"{i:<4}{locked}{host:<16}{uid:<12}{cur}/{mx:<4} {device_id:<6}{ping}ms\n"
        e.description = header + f"```\n{rows}```"

    e.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


def embed_profile(data, err):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)

    uin = data["uin"]
    profile = data.get("profile") or {}
    items = data.get("items")

    e = discord.Embed(title=f"Player Profile — UIN {uin}", color=0xe67e22)

    if profile.get("NickName"):
        e.add_field(name="Nickname", value=profile["NickName"], inline=True)
    if profile.get("Gender"):
        e.add_field(name="Gender", value=profile["Gender"], inline=True)
    if profile.get("Country"):
        e.add_field(name="Country", value=profile["Country"], inline=True)
    if profile.get("Bio"):
        e.add_field(name="Bio", value=profile["Bio"][:100], inline=False)
    if profile.get("Popularity"):
        e.add_field(name="Popularity", value=profile["Popularity"], inline=True)
    if profile.get("MiniBean"):
        e.add_field(name="MiniBean", value=profile["MiniBean"], inline=True)
    if profile.get("MiniCoin"):
        e.add_field(name="MiniCoin", value=profile["MiniCoin"], inline=True)
    if profile.get("Diamond"):
        e.add_field(name="Diamond", value=profile["Diamond"], inline=True)
    if profile.get("Frame"):
        e.add_field(name="Frame ID", value=profile["Frame"], inline=True)
    if profile.get("DeviceID"):
        e.add_field(name="Device ID", value=f"`{profile['DeviceID']}`", inline=False)
    if profile.get("Email"):
        e.add_field(name="Email", value=profile["Email"], inline=True)
    if profile.get("CreateDate"):
        e.add_field(name="Created", value=profile["CreateDate"], inline=True)
    if profile.get("LastLogin"):
        e.add_field(name="Last Login", value=profile["LastLogin"], inline=True)
    if profile.get("Following") and profile.get("Followers") and profile.get("Friends"):
        e.add_field(name="Social", value=f"Following: {profile['Following']} | Followers: {profile['Followers']} | Friends: {profile['Friends']}", inline=False)

    if items:
        e.add_field(name="Total Items", value=str(items["total"]), inline=True)
        e.add_field(name="Permanent", value=str(items["perm"]), inline=True)
        e.add_field(name="Temporary", value=str(items["temp"]), inline=True)
        desc = ""
        for p in sorted(items["by_part"].keys()):
            info = items["by_part"][p]
            name = PART_NAMES.get(p, f"Part {p}")
            desc += f"**{name}**: {info['perm']} perm / {info['temp']} temp\n"
        if desc:
            e.add_field(name="Items By Category", value=desc, inline=False)

    if not profile and not items:
        e.description = "No data found for this UIN.\n(Profile data only available for UINs logged in on this PC)"

    e.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


def embed_mapcount(map_id, data, err):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)
    code = data.get("code", -1)
    if code != 0:
        return discord.Embed(description=f"API error: code {code} (auth expired?)", color=0xe74c3c)
    items = data.get("data", {}).get("list", [])
    if not items:
        return discord.Embed(description="No data found.", color=0xe74c3c)
    it = items[0]
    e = discord.Embed(title=f"Map Stats \u2014 {map_id}", color=0x1abc9c)
    e.add_field(name="Online", value=str(it.get("online", 0)), inline=True)
    e.add_field(name="Rooms", value=str(it.get("roomcnt", 0)), inline=True)
    e.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


def embed_recent_maps(data, err):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)
    wids = data.get("map_ids", [])
    e = discord.Embed(title=f"Recent Maps \u2014 UIN {data['uin']}", color=0xe67e22)
    e.add_field(name="Total Maps", value=str(len(wids)), inline=True)
    if wids:
        desc = ""
        for i, w in enumerate(wids[:15], 1):
            desc += f"`{w}`\n"
        if len(wids) > 15:
            desc += f"...and {len(wids) - 15} more"
        e.description = desc
    else:
        e.description = "No recent maps found."
    e.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


def embed_server_config(data, err, section):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)
    cfg = parse_server_config(data)
    if not cfg:
        return discord.Embed(description="No config data.", color=0xe74c3c)

    e = discord.Embed(title=f"Server Config \u2014 {section}", color=0x1abc9c)

    e.add_field(name="Version", value=cfg["version"], inline=True)
    e.add_field(name="Latest", value=cfg["latest_version"], inline=True)
    e.add_field(name="Block", value=cfg["block_type"], inline=True)

    e.add_field(name="Map Server", value=f"`{cfg['map_server']}`", inline=True)
    e.add_field(name="Room Server", value=f"`{cfg['room_server']}`", inline=True)
    e.add_field(name="MA Server", value=f"`{cfg['ma_server']}`", inline=True)

    e.add_field(name="Cloud Rent URL", value=f"`{cfg['cloud_rent_url']}`", inline=False)
    e.add_field(name="Cloud API URL", value=f"`{cfg['cloud_api_url']}`", inline=False)

    e.add_field(name="Cloud Countries", value=str(cfg["cloud_countries"]), inline=True)
    e.add_field(name="Punch Servers", value=str(cfg["punch_servers"]), inline=True)
    e.add_field(name="Proxy Servers", value=str(cfg["proxy_servers"]), inline=True)
    e.add_field(name="Punch Sample", value=f"`{cfg.get('punch_sample', 'N/A')}`", inline=False)

    e.add_field(name="Oversea Env", value=str(cfg["oversea_env"]), inline=True)
    e.add_field(name="Room Name", value=cfg["room_name"], inline=True)

    e.set_footer(text=f"No Auth Required | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


def embed_query_uin(data, err):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)
    info = parse_query_uin(data["raw"])
    e = discord.Embed(title=f"Query UIN \u2014 {data['uin']}", color=0x9b59b6)
    e.add_field(name="UIN", value=data["uin"], inline=True)
    e.add_field(name="Section", value=data["section"], inline=True)
    e.add_field(name="Result Code", value=str(info["result"]), inline=True)
    e.add_field(name="Server IP", value=f"`{info['ip']}`", inline=True)
    e.add_field(name="Server Port", value=str(info["port"]), inline=True)
    e.set_footer(text=f"No Auth Required | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


def embed_motion(data, err):
    if err:
        return discord.Embed(description=f"Error: {err}", color=0xe74c3c)
    raw = data.get("raw", "")
    ret = re.search(r'\["ret"\]=(\d+)', raw)
    ret_code = int(ret.group(1)) if ret else -1
    e = discord.Embed(title=f"Motion Data \u2014 UIN {data['uin']}", color=0xe74c3c)
    if ret_code == 0:
        e.color = 0x2ecc71
        e.add_field(name="Status", value="Success (ret=0)", inline=True)
        act = re.search(r'\["act"\]=\{(.+?)\}', raw)
        if act:
            e.add_field(name="Action Data", value=f"```{act.group(1)[:200]}```", inline=False)
        else:
            e.add_field(name="Action Data", value="Empty (no custom motions)", inline=False)
    else:
        e.add_field(name="Status", value=f"Failed (ret={ret_code})", inline=True)
    e.set_footer(text=f"No Auth Required | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return e


# ============== EVENTS ==============

@bot.event
async def on_ready():
    print(f"[OK] Bot online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"[OK] Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"[!] Sync failed: {e}")
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}menu"))
    if not kick_loop.is_running():
        kick_loop.start()
    bot.add_view(ReportView())


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        usage = {
            "map": f"`{PREFIX}map <UIN>`",
            "profile": f"`{PREFIX}profile <UIN>`",
            "statusdaily": f"`{PREFIX}statusdaily <UIN>`",
            "cek": f"`{PREFIX}cek <UIN>`",
            "recentmaps": f"`{PREFIX}recentmaps <UIN>`",
            "motion": f"`{PREFIX}motion <UIN>`",
            "queryuin": f"`{PREFIX}queryuin <UIN> [section]`",
            "serverconfig": f"`{PREFIX}serverconfig [section]`",
            "mapcount": f"`{PREFIX}mapcount <map_id>`",
            "checkroom": f"`{PREFIX}checkroom`",
            "kick": f"`{PREFIX}kick <UIN>`",
            "sendnotif": f"`{PREFIX}sendnotif <UIN> <msg>`",
            "clearVNHat": f"`{PREFIX}clearVNHat`",
            "clearIDBts": f"`{PREFIX}clearIDBts`",
        }
        cmd = ctx.command.name
        msg = usage.get(cmd, f"`{PREFIX}{cmd}`")
        e = discord.Embed(title="Usage", description=msg, color=0xf39c12)
        await ctx.send(embed=e)
    else:
        print(f"[ERROR] {ctx.command}: {error}")
        e = discord.Embed(title="Error", description=str(error)[:200], color=0xe74c3c)
        await ctx.send(embed=e)


# ============== MENU ==============

@bot.tree.command(name="menu", description="Show all available commands")
async def menu_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=menu_embed())


@bot.command(name="menu")
async def menu_cmd(ctx):
    await ctx.send(embed=menu_embed())


def menu_embed():
    e = discord.Embed(title="Mini World Bot", description="Check any Mini World player data by UIN.\n\n**No-Auth APIs** = works without login token", color=0xf1c40f)
    e.add_field(
        name="Player Commands",
        value=(
            f"`{PREFIX}profile <UIN>` — View player profile (local cache)\n"
            f"`{PREFIX}cek <UIN>` — View full profile via Worker API\n"
            f"`{PREFIX}map <UIN>` — View map history\n"
            f"`{PREFIX}statusdaily <UIN>` — View daily sign-in status\n"
            f"`{PREFIX}recentmaps <UIN>` — Check recent maps touched\n"
            f"`{PREFIX}motion <UIN>` — Check custom motion data\n"
            f"`{PREFIX}queryuin <UIN> [section]` — Query server assignment\n"
        ),
        inline=False,
    )
    e.add_field(
        name="Server & Map Commands (No Auth)",
        value=(
            f"`{PREFIX}serverconfig [section]` — Full server config\n"
            f"`{PREFIX}checkroom` — Check active rooms (Back To School)\n"
            f"`{PREFIX}mapcount <map_id>` — Check map online stats\n"
        ),
        inline=False,
    )
    e.add_field(
        name="Report & Ban Commands",
        value=(
            f"`{PREFIX}setupreport` — Setup báo cáo cheat\n"
            f"`{PREFIX}kick <UIN>` — Kick player via Lua bridge\n"
            f"`{PREFIX}sendnotif <UIN> <msg>` — Send notif ke player\n"
            f"`{PREFIX}clearVNHat` — Kick semua player di room VN Hat\n"
            f"`{PREFIX}clearIDBts` — Kick semua host di room Back to School\n"
            f"`{PREFIX}banlist` — Xem danh sách ban\n"
        ),
        inline=False,
    )
    e.add_field(
        name="Utility",
        value=(
            f"`{PREFIX}changedev` — Change/generate DeviceID\n"
            f"`{PREFIX}menu` — Show this message\n"
        ),
        inline=False,
    )
    e.add_field(
        name="Sections",
        value="`INA` `TH` `SG` `VN` `HK` `TW` `JP` `BR` `RU` `MY` `US`",
        inline=False,
    )
    e.set_footer(text="Mini World API | No-Auth Endpoints")
    return e


# ============== MAP ==============

@bot.tree.command(name="map", description="Check player map history by UIN")
async def map_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    try:
        maps, real_uin = fetch_maps(uin)
        if isinstance(maps, dict) and "error" in maps:
            await interaction.followup.send(f"Error: {maps['error']}")
        else:
            await interaction.followup.send(embed=embed_map(real_uin, maps))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="map")
async def map_cmd(ctx, uin: str = None):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}map <UIN>`")
        return
    try:
        maps, real_uin = fetch_maps(uin)
        if isinstance(maps, dict) and "error" in maps:
            await ctx.send(f"Error: {maps['error']}")
        else:
            await ctx.send(embed=embed_map(real_uin, maps))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== STATUS DAILY ==============

@bot.tree.command(name="statusdaily", description="Check player daily sign-in status by UIN")
async def statusdaily_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    try:
        data, real_uin = fetch_sign_status(uin)
        await interaction.followup.send(embed=embed_sign(real_uin, data))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="statusdaily")
async def statusdaily_cmd(ctx, uin: str = None):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}statusdaily <UIN>`")
        return
    try:
        data, real_uin = fetch_sign_status(uin)
        await ctx.send(embed=embed_sign(real_uin, data))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== CHECK ROOM ==============

class RoomMapChoice(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Back To School [2.0]", value="back_to_school", emoji="🏫"),
            discord.SelectOption(label="Bunny Vs Misra", value="bunny_vs_misra", emoji="🐰"),
        ]
        super().__init__(placeholder="Select map...", options=options)

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        api = ROOM_APIS.get(key)
        await interaction.response.defer()
        try:
            data = fetch_room(key)
            parsed, err = parse_room(data)
            rooms = (parsed or {}).get("rooms", [])
            view = HostProfileView(rooms)
            await interaction.followup.send(embed=embed_room(parsed or {}, err, api["name"]), view=view)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")


class HostChoice(discord.ui.Select):
    def __init__(self, rooms):
        options = []
        for rm in rooms[:25]:
            host = rm.get("uname", "?")[:20]
            uid = rm.get("uin", "?")
            options.append(discord.SelectOption(label=f"{host}", value=str(uid), description=f"UID: {uid}"))
        super().__init__(placeholder="Check Info Profile Host...", options=options)

    async def callback(self, interaction: discord.Interaction):
        uin = self.values[0]
        await interaction.response.defer()
        try:
            data, err = fetch_worker_profile(uin)
            if err:
                await interaction.followup.send(f"Error: {err}")
                return
            profile = parse_worker_profile(data.get("profile", ""))
            maps = parse_worker_maps(data.get("map", ""))
            vip = data.get("vip", {})
            result = {"profile": profile, "maps": maps, "vip": vip}
            await interaction.followup.send(embed=embed_worker_profile(result, None, uin))
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")


class HostProfileView(discord.ui.View):
    def __init__(self, rooms):
        super().__init__(timeout=60)
        if rooms:
            self.add_item(HostChoice(rooms))


class RoomMapView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(RoomMapChoice())


@bot.tree.command(name="checkroom", description="Check active rooms - pilih map")
async def checkroom_slash(interaction: discord.Interaction):
    e = discord.Embed(title="Select Map", description="Select a map to check rooms:", color=0x9b59b6)
    await interaction.response.send_message(embed=e, view=RoomMapView())


@bot.command(name="checkroom")
async def checkroom_cmd(ctx):
    key = "back_to_school"
    api = ROOM_APIS[key]
    try:
        data = fetch_room(key)
        parsed, err = parse_room(data)
        rooms = (parsed or {}).get("rooms", [])
        view = HostProfileView(rooms)
        await ctx.send(embed=embed_room(parsed or {}, err, api["name"]), view=view)
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== PROFILE ==============

@bot.tree.command(name="profile", description="Check player profile by UIN")
async def profile_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    try:
        data, err = fetch_profile(uin)
        await interaction.followup.send(embed=embed_profile(data, err))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="profile")
async def profile_cmd(ctx, uin: str = None):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}profile <UIN>`")
        return
    try:
        data, err = fetch_profile(uin)
        await ctx.send(embed=embed_profile(data, err))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== MAPCOUNT ==============

@bot.tree.command(name="mapcount", description="Check online players and room count for a map")
async def mapcount_slash(interaction: discord.Interaction, map_id: str):
    await interaction.response.defer()
    try:
        data, err = fetch_mapcount(map_id)
        await interaction.followup.send(embed=embed_mapcount(map_id, data, err))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="mapcount")
async def mapcount_cmd(ctx, map_id: str = None):
    if not map_id:
        await ctx.send(f"Usage: `{PREFIX}mapcount <map_id>`")
        return
    try:
        data, err = fetch_mapcount(map_id)
        await ctx.send(embed=embed_mapcount(map_id, data, err))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== RECENT MAPS ==============

@bot.tree.command(name="recentmaps", description="Check recent maps touched by a player")
async def recentmaps_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    try:
        data, err = fetch_recent_maps(uin)
        await interaction.followup.send(embed=embed_recent_maps(data, err))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="recentmaps")
async def recentmaps_cmd(ctx, uin: str = None):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}recentmaps <UIN>`")
        return
    try:
        data, err = fetch_recent_maps(uin)
        await ctx.send(embed=embed_recent_maps(data, err))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== SERVER CONFIG ==============

@bot.tree.command(name="serverconfig", description="Check Mini World server config (no auth)")
async def serverconfig_slash(interaction: discord.Interaction, section: str = "INA"):
    await interaction.response.defer()
    try:
        data, err = fetch_server_config(section)
        await interaction.followup.send(embed=embed_server_config(data, err, section.upper()))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="serverconfig")
async def serverconfig_cmd(ctx, section: str = None):
    if not section:
        section = "INA"
    try:
        data, err = fetch_server_config(section)
        await ctx.send(embed=embed_server_config(data, err, section.upper()))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== QUERY UIN ==============

@bot.tree.command(name="queryuin", description="Query which server a UIN is assigned to (no auth)")
async def queryuin_slash(interaction: discord.Interaction, uin: str, section: str = "TH"):
    await interaction.response.defer()
    try:
        data, err = fetch_query_uin(uin, section)
        await interaction.followup.send(embed=embed_query_uin(data, err))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="queryuin")
async def queryuin_cmd(ctx, uin: str = None, section: str = "TH"):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}queryuin <UIN> [section]`")
        return
    try:
        data, err = fetch_query_uin(uin, section)
        await ctx.send(embed=embed_query_uin(data, err))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== MOTION ==============

@bot.tree.command(name="motion", description="Check custom motion data for a player (no auth)")
async def motion_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    try:
        data, err = fetch_motion(uin)
        await interaction.followup.send(embed=embed_motion(data, err))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="motion")
async def motion_cmd(ctx, uin: str = None):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}motion <UIN>`")
        return
    try:
        data, err = fetch_motion(uin)
        await ctx.send(embed=embed_motion(data, err))
    except Exception as e:
        await ctx.send(f"Error: {e}")


# ============== CHANGEDEV ==============

def generate_device_id():
    hex_chars = string.hexdigits[:16]
    rand_hex = ''.join(random.choices(hex_chars, k=32))
    return f"WIN{rand_hex}"


def update_registry_device_id(new_id):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\SysDevice_Miniw", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "deviceidd", 0, winreg.REG_SZ, new_id)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        return str(e)


def update_config_files(new_id):
    paths = [
        os.path.expanduser(r"~\AppData\Roaming\miniworldOverseasgame\devices\iworld_1.cfg"),
        os.path.expanduser(r"~\AppData\Roaming\miniworddata410\iworld_1.cfg"),
    ]
    updated = []
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                new_content = re.sub(
                    r'(DeviceID\s*=\s*\[\[)[^\]]*(\]\])',
                    f'\\g<1>{new_id}\\2',
                    content
                )
                if new_content == content:
                    new_content = re.sub(
                        r'(deviceidd\s*=\s*")[^"]*(")',
                        f'\\g<1>{new_id}\\2',
                        content
                    )
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated.append(os.path.basename(p))
            except Exception as e:
                updated.append(f"{os.path.basename(p)}: ERROR {e}")
    return updated


def apply_device_id(new_id):
    reg_result = update_registry_device_id(new_id)
    config_results = update_config_files(new_id)
    return reg_result, config_results


class DevIDRandomButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Random", style=discord.ButtonStyle.green, emoji="🎲")

    async def callback(self, interaction: discord.Interaction):
        new_id = generate_device_id()
        reg_result, config_results = apply_device_id(new_id)
        if reg_result is not True:
            await interaction.response.edit_message(content=f"Registry error: {reg_result}", view=None)
            return
        e = discord.Embed(title="DeviceID Changed", color=0x2ecc71)
        e.add_field(name="New DeviceID", value=f"`{new_id}`", inline=False)
        config_str = "\n".join(f"- {r}" for r in config_results)
        e.add_field(name="Updated", value=config_str, inline=False)
        e.add_field(name="Note", value="Restart game to apply.", inline=False)
        await interaction.response.edit_message(embed=e, view=None)


class DevIDCustomButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Custom", style=discord.ButtonStyle.blurple, emoji="✏️")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DevIDModal())


class DevIDModal(discord.ui.Modal, title="Enter DeviceID"):
    device_id = discord.ui.TextInput(
        label="DeviceID (WIN + 32 hex chars)",
        placeholder="WIN1eec8d7b5411d74cfcb64b17e3cf12ee",
        required=True,
        max_length=36,
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_id = self.device_id.value.strip()
        if not re.match(r'^WIN[0-9a-fA-F]{32}$', new_id):
            await interaction.response.send_message(
                f"Invalid format.\nFormat: `WIN` + 32 hex chars\nExample: `WIN1eec8d7b5411d74cfcb64b17e3cf12ee`",
                ephemeral=True,
            )
            return
        reg_result, config_results = apply_device_id(new_id)
        if reg_result is not True:
            await interaction.response.send_message(f"Registry error: {reg_result}", ephemeral=True)
            return
        e = discord.Embed(title="DeviceID Changed", color=0x2ecc71)
        e.add_field(name="New DeviceID", value=f"`{new_id}`", inline=False)
        config_str = "\n".join(f"- {r}" for r in config_results)
        e.add_field(name="Updated", value=config_str, inline=False)
        e.add_field(name="Note", value="Restart game to apply.", inline=False)
        await interaction.response.send_message(embed=e, ephemeral=True)


class DevIDView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DevIDRandomButton())
        self.add_item(DevIDCustomButton())


@bot.tree.command(name="changedev", description="Change or generate DeviceID")
async def changedev_slash(interaction: discord.Interaction):
    e = discord.Embed(title="Change DeviceID", description="Choose an option:", color=0xf39c12)
    await interaction.response.send_message(embed=e, view=DevIDView(), ephemeral=True)


@bot.command(name="changedev")
async def changedev_cmd(ctx):
    e = discord.Embed(title="Change DeviceID", description="Choose an option:", color=0xf39c12)
    await ctx.send(embed=e, view=DevIDView())


# ============== WORKER PROFILE COMMAND ==============

@bot.tree.command(name="cek", description="Check player profile via Worker API (full data)")
async def cek_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    try:
        real_uin = fix_uin(uin)
        data, err = fetch_worker_profile(real_uin)
        if err:
            await interaction.followup.send(f"Error: {err}")
            return
        profile = parse_worker_profile(data.get("profile", ""))
        maps = parse_worker_maps(data.get("map", ""))
        vip = data.get("vip", {})
        result = {"profile": profile, "maps": maps, "vip": vip}
        await interaction.followup.send(embed=embed_worker_profile(result, None, real_uin))
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@bot.command(name="cek")
async def cek_cmd(ctx, uin: str = None):
    if not uin:
        await ctx.send(f"Usage: `{PREFIX}cek <UIN>`")
        return
    load_embed = discord.Embed(title="Loading...", description="**Load player data..**", color=0xf1c40f)
    msg = await ctx.send(embed=load_embed)
    try:
        real_uin = fix_uin(uin)
        data, err = fetch_worker_profile(real_uin)
        if err:
            err_embed = discord.Embed(title="Error", description=str(err), color=0xe74c3c)
            await msg.edit(embed=err_embed)
            return
        profile = parse_worker_profile(data.get("profile", ""))
        maps = parse_worker_maps(data.get("map", ""))
        vip = data.get("vip", {})
        result = {"profile": profile, "maps": maps, "vip": vip}
        await msg.edit(embed=embed_worker_profile(result, None, real_uin))
    except Exception as e:
        err_embed = discord.Embed(title="Error", description=str(e), color=0xe74c3c)
        await msg.edit(embed=err_embed)


# ============== REPORT SYSTEM ==============

def format_duration(seconds):
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


async def fetch_profile_for_report(uin):
    try:
        raw_uin = str(uin).strip()

        def do_fetch():
            url = f"https://profile-acc.event-miniworld.workers.dev/get={raw_uin}"
            r = requests.get(url, timeout=10)
            return r.json() if r.status_code == 200 else None

        data = await asyncio.to_thread(do_fetch)
        if not data or data.get("code") != 0:
            return None
        profile_str = data.get("profile", "")
        if not profile_str:
            return None

        profile = {}
        m = re.search(r'\["NickName"\]\s*=\s*"([^"]*)"', profile_str)
        if m:
            profile["nickname"] = m.group(1)

        m = re.search(r'\["url"\]\s*=\s*"([^"]*)"', profile_str)
        if m:
            profile["avatar"] = m.group(1)

        m = re.search(r'\["country"\]\s*=\s*"([^"]*)"', profile_str)
        if m:
            profile["country"] = m.group(1)

        m = re.search(r'\["friend_eachother"\]\s*=\s*(\d+)', profile_str)
        if m:
            profile["friends"] = m.group(1)

        m = re.search(r'\["friend_beattention"\]\s*=\s*(\d+)', profile_str)
        if m:
            profile["followers"] = m.group(1)

        m = re.search(r'\["friend_attention"\]\s*=\s*(\d+)', profile_str)
        if m:
            profile["following"] = m.group(1)

        m = re.search(r'\["popularity"\]\s*=\s*(\d+)', profile_str)
        if m:
            profile["popularity"] = m.group(1)

        m = re.search(r'\["mood_text"\]\s*=\s*"([^"]*)"', profile_str)
        if m:
            profile["mood"] = m.group(1)

        return profile if profile else None
    except Exception as e:
        print(f"[PROFILE] Error fetching {uin}: {e}")
        return None


def build_ban_info_embed(uin, info, profile=None):
    remaining = max(0, info["expires_at"] - time.time())
    days_banned = (time.time() - info["started_at"]) / 86400
    last_update = datetime.fromtimestamp(info["started_at"]).strftime("%d/%m/%Y %H:%M:%S")

    nickname = "Unknown"
    avatar = None
    if profile:
        nickname = profile.get("nickname") or "Unknown"
        avatar = profile.get("avatar")

    e = discord.Embed(title=f"BAN | {nickname}", color=0xe74c3c)
    if avatar:
        e.set_thumbnail(url=avatar)

    e.add_field(name="INFORMATION", value="", inline=False)
    e.add_field(name="UID", value=f"`{uin}`", inline=True)
    e.add_field(name="Reason", value=info["reason"][:100], inline=False)
    e.add_field(name="Ban Type", value="Account" if info.get("ban_type") == "acc" else "Device", inline=True)
    e.add_field(name="Duration", value=format_duration(remaining), inline=True)
    e.add_field(name="Total Kicks", value=str(info["kick_count"]), inline=True)
    e.add_field(name="Days Banned", value=f"{days_banned:.1f} / 12.0", inline=True)
    e.set_footer(text=f"Updated: {last_update} | Expires in {format_duration(remaining)}")
    return e


class PunishAccButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ban Acc (12 days)", style=discord.ButtonStyle.danger, emoji="1️⃣")

    async def callback(self, interaction):
        self.view.selected = "acc"
        self.view.stop()


class PunishDeviceButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ban Device (12 days)", style=discord.ButtonStyle.danger, emoji="2️⃣")

    async def callback(self, interaction):
        self.view.selected = "device"
        self.view.stop()


class PunishSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.selected = None
        self.add_item(PunishAccButton())
        self.add_item(PunishDeviceButton())

    async def on_timeout(self):
        self.selected = None
        self.stop()


class ReportModal(discord.ui.Modal, title="Report Cheat"):
    uid = discord.ui.TextInput(label="Player UID", placeholder="Enter target UID...", required=True, max_length=20)
    streamable = discord.ui.TextInput(label="Streamable Link", placeholder="https://streamable.com/...", required=True)
    reason = discord.ui.TextInput(label="Reason", placeholder="Why are you reporting this player...", required=True, style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction):
        try:
            global REPORT_STATS
            REPORT_STATS["total"] += 1
            REPORT_STATS["reporters"].add(interaction.user.id)

            real_uin = fix_uin(self.uid.value)

            punish_view = PunishSelectView()
            e = discord.Embed(title="SELECT PUNISHMENT", description="Choose a punishment for this player:", color=0xf39c12)
            e.add_field(name="UID", value=f"`{real_uin}`", inline=True)
            e.add_field(name="Reporter", value=interaction.user.mention, inline=True)
            e.add_field(name="Reason", value=self.reason.value, inline=False)
            e.set_footer(text="60 seconds to choose | Timeout = auto cancel")

            await interaction.response.send_message(embed=e, view=punish_view, ephemeral=True)

            await punish_view.wait()

            if punish_view.selected is None:
                try:
                    await interaction.edit_original_response(content="Timed out. Report cancelled.", embed=None, view=None)
                except:
                    pass
                return

            ban_type = punish_view.selected

            report_embed = discord.Embed(title="NEW REPORT", color=0xf39c12)
            report_embed.add_field(name="UID", value=f"`{real_uin}`", inline=True)
            report_embed.add_field(name="Reporter", value=interaction.user.mention, inline=True)
            report_embed.add_field(name="Punishment", value=f"Ban {'Account' if ban_type == 'acc' else 'Device'} (12 days)", inline=True)
            report_embed.add_field(name="Reason", value=self.reason.value, inline=False)
            report_embed.add_field(name="Streamable", value=self.streamable.value, inline=False)
            report_embed.set_footer(text=f"Report #{REPORT_STATS['total']} | Active bans: {REPORT_STATS['banned']}/50 | Duration: 12 days")

            profile = await fetch_profile_for_report(real_uin)
            if profile:
                nickname = profile.get("nickname") or "Unknown"
                avatar = profile.get("avatar")
                report_embed.title = f"NEW REPORT — {nickname}"
                if avatar:
                    report_embed.set_thumbnail(url=avatar)

            view = ApproveRejectView(real_uin, self.streamable.value, self.reason.value, interaction.user.id, ban_type)
            report_channel = interaction.client.get_channel(REPORT_CHANNEL_ID)
            if report_channel:
                await report_channel.send(embed=report_embed, view=view)

            try:
                await interaction.edit_original_response(content="✅ Report submitted!", embed=None, view=None)
            except:
                pass
        except Exception as ex:
            print(f"[REPORT] Error: {ex}")

    async def on_error(self, interaction, error):
        print(f"[MODAL ERROR] {error}")
        try:
            await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)
        except:
            try:
                await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)
            except:
                pass


BAN_LOG_CHANNEL_ID = 1543862919710769182
REPORT_CHANNEL_ID = 1543954325867331594


class ApproveRejectButton(discord.ui.Button):
    def __init__(self, action, uin, streamable, reason, reporter_id, ban_type="acc"):
        if action == "approve":
            super().__init__(label="Approve Ban", style=discord.ButtonStyle.green, emoji="✅")
        else:
            super().__init__(label="Reject", style=discord.ButtonStyle.red, emoji="❌")
        self.action = action
        self.uin = uin
        self.streamable = streamable
        self.reason = reason
        self.reporter_id = reporter_id
        self.ban_type = ban_type

    async def callback(self, interaction):
        global REPORT_STATS
        if self.action == "approve":
            await interaction.response.edit_message(content="✅ Processing ban...", view=None)

            ACTIVE_BANS[self.uin] = {
                "reason": self.reason,
                "streamable": self.streamable,
                "reporter": self.reporter_id,
                "ban_type": self.ban_type,
                "started_at": time.time(),
                "expires_at": time.time() + (12 * 24 * 3600),
                "kick_count": 0,
            }
            REPORT_STATS["banned"] += 1

            lua = KICK_LUA.format(uin=self.uin)
            kick_result = await send_lua_via_bridge(lua)

            profile = await fetch_profile_for_report(self.uin)
            info = ACTIVE_BANS[self.uin]
            e = build_ban_info_embed(self.uin, info, profile)
            e.add_field(name="First Kick", value=f"`{kick_result}`", inline=False)
            try:
                await interaction.edit_original_response(embed=e)
            except:
                pass

            try:
                reporter = await interaction.client.fetch_user(self.reporter_id)
                if reporter:
                    rn = "Unknown"
                    if profile:
                        rn = profile.get("nickname") or "Unknown"
                    notify_channel = interaction.client.get_channel(REPORT_CHANNEL_ID)
                    if notify_channel:
                        ne = discord.Embed(description=f"Report accepted! UID `{self.uin}` ({rn}) has been banned for 12 days.", color=0x2ecc71)
                        await notify_channel.send(embed=ne)
            except:
                pass

            try:
                log_channel = interaction.client.get_channel(BAN_LOG_CHANNEL_ID)
                if log_channel:
                    log_e = build_ban_info_embed(self.uin, info, profile)
                    await log_channel.send(embed=log_e)
            except:
                pass
        else:
            e = discord.Embed(title="Report Rejected", description=f"UID `{self.uin}`", color=0xe74c3c)
            await interaction.response.edit_message(embed=e, view=None)
            try:
                reporter = await interaction.client.fetch_user(self.reporter_id)
                if reporter:
                    re = discord.Embed(title="Report Rejected", description=f"UID `{self.uin}` has been rejected.", color=0xe74c3c)
                    await reporter.send(embed=re)
            except:
                pass


class ApproveRejectView(discord.ui.View):
    def __init__(self, uin, streamable, reason, reporter_id, ban_type="acc"):
        super().__init__(timeout=None)
        self.add_item(ApproveRejectButton("approve", uin, streamable, reason, reporter_id, ban_type))
        self.add_item(ApproveRejectButton("reject", uin, streamable, reason, reporter_id, ban_type))


class ReportButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Report", style=discord.ButtonStyle.danger, emoji="⚠️")

    async def callback(self, interaction):
        await interaction.response.send_modal(ReportModal())


class ReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ReportButton())


@tasks.loop(seconds=15)
async def kick_loop():
    now = time.time()
    to_remove = []
    for uin, info in list(ACTIVE_BANS.items()):
        if now > info["expires_at"]:
            to_remove.append(uin)
            continue
        lua = KICK_LUA.format(uin=uin)
        result = await send_lua_via_bridge(lua)
        info["kick_count"] += 1
        print(f"[KICK] UIN {uin} #{info['kick_count']}: {result}")

    for uin in to_remove:
        try:
            notify_channel = bot.get_channel(REPORT_CHANNEL_ID)
            if notify_channel:
                ne = discord.Embed(title="Ban Expired", description=f"UID `{uin}` ban has expired (12 days).", color=0xf39c12)
                await notify_channel.send(embed=ne)
        except:
            pass
        del ACTIVE_BANS[uin]


@kick_loop.before_loop
async def before_kick_loop():
    await bot.wait_until_ready()


@bot.command(name="setupreport")
async def setupreport_cmd(ctx):
    e = discord.Embed(
        title="REPORT CHEAT",
        description=(
            "Click the button below to report a cheater.\n"
            "If it doesn't respond, try clicking again (don't spam).\n\n"
            "**How to:**\n"
            "1. Click **Report**\n"
            "2. Enter UID, reason, Streamable link\n"
            "3. Admin reviews → Auto ban\n\n"
            "**Duration:** 12 days"
        ),
        color=0xe74c3c,
    )
    e.set_footer(text="Anti Destroy")
    await ctx.send(embed=e, view=ReportView())


@bot.tree.command(name="setupreport", description="Setup report system")
async def setupreport_slash(interaction: discord.Interaction):
    e = discord.Embed(
        title="REPORT CHEAT",
        description=(
            "Click the button below to report a cheater.\n"
            "If it doesn't respond, try clicking again (don't spam).\n\n"
            "**How to:**\n"
            "1. Click **Report**\n"
            "2. Enter UID, reason, Streamable link\n"
            "3. Admin reviews → Auto ban\n\n"
            "**Duration:** 12 days"
        ),
        color=0xe74c3c,
    )
    e.set_footer(text="Anti Destroy")
    await interaction.response.send_message(embed=e, view=ReportView())


@bot.command(name="kick")
async def kick_cmd(ctx, uin: str = None):
    if not uin:
        e = discord.Embed(title="Usage", description=f"`{PREFIX}kick <UIN>`", color=0xf39c12)
        await ctx.send(embed=e)
        return
    real_uin = fix_uin(uin)
    lua = KICK_LUA.format(uin=real_uin)
    result = await send_lua_via_bridge(lua)
    e = discord.Embed(title=f"Kick {real_uin}", color=0xe74c3c)
    e.add_field(name="UID", value=f"`{real_uin}`", inline=True)
    e.add_field(name="Result", value=str(result), inline=False)
    await ctx.send(embed=e)


@bot.tree.command(name="kick", description="Kick player via Lua bridge")
async def kick_slash(interaction: discord.Interaction, uin: str):
    await interaction.response.defer()
    real_uin = fix_uin(uin)
    lua = KICK_LUA.format(uin=real_uin)
    result = await send_lua_via_bridge(lua)
    e = discord.Embed(title=f"Kick {real_uin}", color=0xe74c3c)
    e.add_field(name="UID", value=f"`{real_uin}`", inline=True)
    e.add_field(name="Result", value=str(result), inline=False)
    await interaction.followup.send(embed=e)


# ============== SEND NOTIF ==============

@bot.command(name="sendnotif")
async def sendnotif_cmd(ctx, uin: str = None, *, text: str = None):
    if not uin or not text:
        e = discord.Embed(title="Usage", description=f"`{PREFIX}sendnotif <UIN> <message>`\n\nExample: `{PREFIX}sendnotif 1923123 Gay`", color=0xf39c12)
        await ctx.send(embed=e)
        return
    real_uin = fix_uin(uin)
    lua = NOTIF_LUA.format(uin=real_uin, text=text.replace('"', '\\"'))
    result = await send_lua_via_bridge(lua)
    e = discord.Embed(title=f"Notif → {real_uin}", color=0x3498db)
    e.add_field(name="UID", value=f"`{real_uin}`", inline=True)
    e.add_field(name="Message", value=text[:200], inline=False)
    e.add_field(name="Result", value=str(result), inline=False)
    await ctx.send(embed=e)


@bot.tree.command(name="sendnotif", description="Send notification to a player via Lua bridge")
async def sendnotif_slash(interaction: discord.Interaction, uin: str, text: str):
    await interaction.response.defer()
    real_uin = fix_uin(uin)
    lua = NOTIF_LUA.format(uin=real_uin, text=text.replace('"', '\\"'))
    result = await send_lua_via_bridge(lua)
    e = discord.Embed(title=f"Notif → {real_uin}", color=0x3498db)
    e.add_field(name="UID", value=f"`{real_uin}`", inline=True)
    e.add_field(name="Message", value=text[:200], inline=False)
    e.add_field(name="Result", value=str(result), inline=False)
    await interaction.followup.send(embed=e)


# ============== CLEAR VN HAT ==============

HAT_API_URL = "https://gentle-cloud-e627.daxtercarl1202.workers.dev/"
HAT_MAP_TYPE = "36521411564844"


def fetch_hat_rooms():
    try:
        r = requests.get(HAT_API_URL, timeout=15)
        if r.status_code == 200:
            return r.json(), None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def parse_hat_hosts(data):
    hosts = []
    if not data:
        return hosts
    roomlist = data.get("roomlist", [])
    if not isinstance(roomlist, list):
        roomlist = []
    rent = data.get("rent", [])
    if not isinstance(rent, list):
        rent = []
    all_rooms = roomlist + rent
    for rm in all_rooms:
        map_type = str(rm.get("map_type", ""))
        if map_type == HAT_MAP_TYPE:
            uin = rm.get("uin")
            uname = rm.get("uname", "?")
            cur = rm.get("cur_count", 0)
            mx = rm.get("max_count", 0)
            if uin:
                hosts.append({"uin": str(uin), "uname": uname, "cur": cur, "max": mx})
    return hosts


@bot.command(name="clearVNHat")
async def clearvnh_cmd(ctx):
    load_e = discord.Embed(title="Loading...", description="Fetching Hat rooms from API...", color=0xf1c40f)
    msg = await ctx.send(embed=load_e)

    data, err = fetch_hat_rooms()
    if err:
        e = discord.Embed(title="Error", description=err, color=0xe74c3c)
        await msg.edit(embed=e)
        return

    hosts = parse_hat_hosts(data)
    if not hosts:
        e = discord.Embed(title="Clear VN Hat", description="No active Hat rooms found.", color=0xe74c3c)
        await msg.edit(embed=e)
        return

    results = []
    for h in hosts:
        real_uin = fix_uin(h["uin"])
        lua = KICK_LUA.format(uin=real_uin)
        kick_result = await send_lua_via_bridge(lua)
        results.append({"uin": real_uin, "uname": h["uname"], "players": f"{h['cur']}/{h['max']}", "result": kick_result})

    e = discord.Embed(title="Clear VN Hat — Done", color=0xe74c3c)
    for r in results:
        e.add_field(
            name=f"{r['uname']} ({r['uin']})",
            value=f"Players: {r['players']}\nResult: `{r['result']}`",
            inline=False,
        )
    e.set_footer(text=f"Total rooms cleared: {len(results)} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await msg.edit(embed=e)


@bot.tree.command(name="clearvnhat", description="Kick all players in VN Hat rooms")
async def clearvnh_slash(interaction: discord.Interaction):
    await interaction.response.defer()

    data, err = fetch_hat_rooms()
    if err:
        e = discord.Embed(title="Error", description=err, color=0xe74c3c)
        await interaction.followup.send(embed=e)
        return

    hosts = parse_hat_hosts(data)
    if not hosts:
        e = discord.Embed(title="Clear VN Hat", description="No active Hat rooms found.", color=0xe74c3c)
        await interaction.followup.send(embed=e)
        return

    results = []
    for h in hosts:
        real_uin = fix_uin(h["uin"])
        lua = KICK_LUA.format(uin=real_uin)
        kick_result = await send_lua_via_bridge(lua)
        results.append({"uin": real_uin, "uname": h["uname"], "players": f"{h['cur']}/{h['max']}", "result": kick_result})

    e = discord.Embed(title="Clear VN Hat — Done", color=0xe74c3c)
    for r in results:
        e.add_field(
            name=f"{r['uname']} ({r['uin']})",
            value=f"Players: {r['players']}\nResult: `{r['result']}`",
            inline=False,
        )
    e.set_footer(text=f"Total rooms cleared: {len(results)} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await interaction.followup.send(embed=e)


# ============== CLEAR ID BTS ==============

def parse_bts_hosts(data):
    hosts = []
    if not data:
        return hosts
    # handle parsed data from parse_room (has "rooms")
    if "rooms" in data:
        for rm in data.get("rooms", []) or []:
            uin = rm.get("uin")
            uname = rm.get("uname", "?")
            cur = rm.get("cur_count", 0)
            mx = rm.get("max_count", 0)
            if uin:
                hosts.append({"uin": str(uin), "uname": uname, "cur": cur, "max": mx})
        return hosts
    roomlist = data.get("roomlist", [])
    if not isinstance(roomlist, list):
        roomlist = []
    rent = data.get("rent", [])
    if not isinstance(rent, list):
        rent = []
    all_rooms = roomlist + rent
    for rm in all_rooms:
        uin = rm.get("uin")
        uname = rm.get("uname", "?")
        cur = rm.get("cur_count", 0)
        mx = rm.get("max_count", 0)
        if uin:
            hosts.append({"uin": str(uin), "uname": uname, "cur": cur, "max": mx})
    return hosts


@bot.command(name="clearIDBts")
async def clearidbts_cmd(ctx):
    load_e = discord.Embed(title="Loading...", description="Fetching Back to School rooms from API...", color=0xf1c40f)
    msg = await ctx.send(embed=load_e)

    data = fetch_room("back_to_school")
    if "error" in data:
        e = discord.Embed(title="Error", description=data["error"], color=0xe74c3c)
        await msg.edit(embed=e)
        return

    parsed, err2 = parse_room(data)
    if err2:
        e = discord.Embed(title="Error", description=err2, color=0xe74c3c)
        await msg.edit(embed=e)
        return

    hosts = parse_bts_hosts(parsed)
    if not hosts:
        e = discord.Embed(title="Clear ID BTS", description="No active Back to School rooms found.", color=0xe74c3c)
        await msg.edit(embed=e)
        return

    results = []
    for h in hosts:
        real_uin = fix_uin(h["uin"])
        lua = KICK_LUA.format(uin=real_uin)
        kick_result = await send_lua_via_bridge(lua)
        results.append({"uin": real_uin, "uname": h["uname"], "players": f"{h['cur']}/{h['max']}", "result": kick_result})

    e = discord.Embed(title="Clear ID BTS — Done", color=0xe74c3c)
    for r in results:
        e.add_field(
            name=f"{r['uname']} ({r['uin']})",
            value=f"Players: {r['players']}\nResult: `{r['result']}`",
            inline=False,
        )
    e.set_footer(text=f"Total hosts kicked: {len(results)} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await msg.edit(embed=e)


@bot.tree.command(name="clearidbts", description="Kick all hosts in Back to School rooms")
async def clearidbts_slash(interaction: discord.Interaction):
    await interaction.response.defer()

    data = fetch_room("back_to_school")
    if "error" in data:
        e = discord.Embed(title="Error", description=data["error"], color=0xe74c3c)
        await interaction.followup.send(embed=e)
        return

    parsed, err2 = parse_room(data)
    if err2:
        e = discord.Embed(title="Error", description=err2, color=0xe74c3c)
        await interaction.followup.send(embed=e)
        return

    hosts = parse_bts_hosts(parsed)
    if not hosts:
        e = discord.Embed(title="Clear ID BTS", description="No active Back to School rooms found.", color=0xe74c3c)
        await interaction.followup.send(embed=e)
        return

    results = []
    for h in hosts:
        real_uin = fix_uin(h["uin"])
        lua = KICK_LUA.format(uin=real_uin)
        kick_result = await send_lua_via_bridge(lua)
        results.append({"uin": real_uin, "uname": h["uname"], "players": f"{h['cur']}/{h['max']}", "result": kick_result})

    e = discord.Embed(title="Clear ID BTS — Done", color=0xe74c3c)
    for r in results:
        e.add_field(
            name=f"{r['uname']} ({r['uin']})",
            value=f"Players: {r['players']}\nResult: `{r['result']}`",
            inline=False,
        )
    e.set_footer(text=f"Total hosts kicked: {len(results)} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await interaction.followup.send(embed=e)


@bot.command(name="inject")
async def inject_cmd(ctx):
    if ctx.author.id != OWNER_ID:
        return
    e = discord.Embed(title="Injecting...", description="Injecting LuaExec DLL...", color=0xf39c12)
    msg = await ctx.send(embed=e)
    result = await inject_dll()
    if "error" in result:
        e = discord.Embed(title="Inject Failed", description=result['error'], color=0xe74c3c)
    else:
        msg_text = result.get("message") or str(result)
        e = discord.Embed(title="Inject Success", description=msg_text, color=0x2ecc71)
    await msg.edit(embed=e)


@bot.command(name="banlist")
async def banlist_cmd(ctx):
    if not ACTIVE_BANS:
        await ctx.send("No active bans.")
        return
    e = discord.Embed(title="Active Bans", color=0xe74c3c)
    for uin, info in ACTIVE_BANS.items():
        days_banned = (time.time() - info["started_at"]) / 86400
        remaining = max(0, info["expires_at"] - time.time())
        profile = await fetch_profile_for_report(uin)
        nickname = "Unknown"
        avatar = None
        if profile:
            nickname = profile.get("nickname") or "Unknown"
            avatar = profile.get("avatar")
        e.add_field(
            name=f"{nickname} ({uin})",
            value=(
                f"Reason: {info['reason'][:60]}\n"
                f"Kicks: {info['kick_count']} | Days: {days_banned:.1f}/12 | Left: {format_duration(remaining)}"
            ),
            inline=False,
        )
        if avatar:
            e.set_thumbnail(url=avatar)
    e.set_footer(text=f"Total: {len(ACTIVE_BANS)} | Reports: {REPORT_STATS['total']} | Banned: {REPORT_STATS['banned']}")
    await ctx.send(embed=e)


@bot.command(name="cancelban")
async def cancelban_cmd(ctx):
    if ctx.author.id != OWNER_ID:
        return
    count = len(ACTIVE_BANS)
    ACTIVE_BANS.clear()
    e = discord.Embed(title="All Bans Cancelled", description=f"Cleared **{count}** active bans.\nKick loops stopped.", color=0x2ecc71)
    await ctx.send(embed=e)


@bot.tree.command(name="cancelban", description="Cancel all bans (owner only)")
async def cancelban_slash(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        return
    count = len(ACTIVE_BANS)
    ACTIVE_BANS.clear()
    e = discord.Embed(title="All Bans Cancelled", description=f"Cleared **{count}** active bans.\nKick loops stopped.", color=0x2ecc71)
    await interaction.response.send_message(embed=e)


# ============== MAIN ==============

if __name__ == "__main__":
    print("=" * 50)
    print("  Mini World Bot")
    print("=" * 50)
    print(f"  Prefix : {PREFIX}")
    print(f"  Commands: menu, profile, cek, map, statusdaily, checkroom, mapcount, recentmaps, serverconfig, queryuin, motion, changedev, setupreport, kick, sendnotif, clearVNHat, clearIDBts, banlist")
    print("=" * 50)
    bot.run(TOKEN)
