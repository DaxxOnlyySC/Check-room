# Mini World Discord Bot

Discord bot untuk Mini World — check room, profile, report cheat, kick via Lua bridge.

## Features

- `?setupreport` — Setup report cheat system (button + modal)
- `?kick <UIN>` — Kick player via Lua bridge
- `?inject` — Inject LuaExec DLL (owner only)
- `?banlist` — List active bans
- `?profile <UIN>` — Check player profile
- `?cek <UIN>` — Full profile via Worker API
- `?map <UIN>` — Map history
- `?checkroom` — Check active rooms
- `?serverconfig` — Server config
- And more...

## Architecture

```
[Railway Bot (main.py)]  -->  [Bridge Server (bridge_server.py)]  -->  [Game (LuaExec)]
       (Cloud)                        (Your PC)                         (MiniWorld)
```

- **Railway** runs the Discord bot (`main.py`) in the cloud
- **Bridge Server** (`bridge_server.py`) runs on your PC — receives commands from Railway via HTTP, sends Lua code to game via named pipe
- **Ngrok** tunnels Railway → your local bridge server

## Setup

### 1. Railway (Cloud Bot)

1. Fork this repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set these **Environment Variables** in Railway:

| Variable | Value | Notes |
|----------|-------|-------|
| `DISCORD_TOKEN` | Your Discord bot token | From Discord Developer Portal |
| `PREFIX` | `?` | Command prefix |
| `MW_UIN` | Your MiniWorld UIN | e.g. `1210244113` |
| `MW_AUTH` | Your MiniWorld auth key | From login |
| `BOT_OWNER_ID` | Your Discord User ID | Right-click your name → Copy User ID |
| `BRIDGE_URL` | Your ngrok URL | e.g. `https://abc123.ngrok-free.app` |
| `AUTH_TOKEN` | `mwbot_secret_2024` | Must match bridge_server.py |

4. Railway will auto-deploy using the Dockerfile

### 2. Bridge Server (Your PC)

1. Install Python 3.12+ on your PC
2. Clone this repo or download the files
3. Install dependencies:
```bash
pip install -r requirements.txt
pip install pywin32 psutil
```

4. Create `.env` file (copy from `env.example`):
```env
DISCORD_TOKEN=your_token
PREFIX=?
MW_UIN=your_uin
MW_AUTH=your_auth
BOT_OWNER_ID=your_discord_id
BRIDGE_URL=http://localhost:18234
AUTH_TOKEN=mwbot_secret_2024
LUAEXEC_PIPE=\\.\pipe\your_pipe_name
SECRET_KEY=your_secret_key
INJECT_EXE=C:\path\to\injectdll.exe
INJECT_DLL=C:\path\to\LuaExec.dll
```

5. Run bridge server:
```bash
python bridge_server.py
```

### 3. Ngrok (Tunnel)

1. Install ngrok: https://ngrok.com
2. Run:
```bash
ngrok http 18234
```
3. Copy the `https://xxx.ngrok-free.app` URL
4. Paste it as `BRIDGE_URL` in Railway environment variables

### 4. LuaExec (Game)

1. Open MiniWorld game
2. Inject LuaExec DLL (use `?inject` command in Discord or manual inject)
3. The bridge server will connect to the game via named pipe

## Railway Environment Variables Summary

```
DISCORD_TOKEN=MTUxNTAyOTA3MzU5ODg3MzYxMA.GS45pX.xxx
PREFIX=?
MW_UIN=1254160075
MW_AUTH=44be0e81c1b9a267a8e5e85c215aaa33
BOT_OWNER_ID=1286240448775720962
BRIDGE_URL=https://your-ngrok-url.ngrok-free.app
AUTH_TOKEN=mwbot_secret_2024
```

## Files

| File | Runs on | Purpose |
|------|---------|---------|
| `main.py` | Railway (cloud) | Discord bot |
| `bridge_server.py` | Your PC | HTTP bridge → game pipe |
| `worker.js` | Cloudflare | Room proxy API |
| `Dockerfile` | Railway | Container build |
| `railway.toml` | Railway | Deploy config |

## Commands

| Command | Description |
|---------|-------------|
| `?menu` | Show all commands |
| `?setupreport` | Setup cheat report system |
| `?kick <UIN>` | Kick player via Lua |
| `?inject` | Inject DLL (owner only) |
| `?banlist` | List active bans |
| `?profile <UIN>` | Check profile (local cache) |
| `?cek <UIN>` | Full profile (Worker API) |
| `?map <UIN>` | Map history |
| `?statusdaily <UIN>` | Daily sign status |
| `?checkroom` | Check active rooms |
| `?mapcount <map_id>` | Map online stats |
| `?recentmaps <UIN>` | Recent maps |
| `?serverconfig [section]` | Server config |
| `?queryuin <UIN> [section]` | Query server assignment |
| `?motion <UIN>` | Custom motion data |
| `?changedev` | Change DeviceID |
