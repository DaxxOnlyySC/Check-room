@echo off
echo Starting MiniGameApp hidden + bridge for gm.kick 1320454366
cd /d "%~dp0"
start "" /min "C:\Users\daxxx\AppData\Roaming\miniworldOverseasgame\MiniGameApp.exe"
timeout /t 10
start "" python bridge_server.py
echo MiniGameApp running hidden - use ?kick 1320454366 in Discord
pause
