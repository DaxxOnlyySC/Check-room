"""Try to get PID from MiniGameApp.exe even without window, then gm.kick"""
import psutil, subprocess, time, os

TARGET = "1320454366"
EXE = r"C:\Users\daxxx\AppData\Roaming\miniworldOverseasgame\MiniGameApp.exe"

print("Checking MiniGameApp PID...")
found = None
for p in psutil.process_iter(['pid','name']):
    if p.info['name'] == 'MiniGameApp.exe':
        found = p.info['pid']
        break
if found:
    print(f"Found PID {found} - can gm.kick {TARGET} via bridge")
else:
    print("No PID - MiniGameApp not running")
    print(f"Trying to start hidden {EXE}...")
    try:
        # start hidden
        subprocess.Popen([EXE], creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(8)
        for p in psutil.process_iter(['pid','name']):
            if p.info['name'] == 'MiniGameApp.exe':
                print(f"Started PID {p.info['pid']}")
                found = p.info['pid']
                break
    except Exception as e:
        print(f"start err {e}")

if found:
    print(f"Ready to gm.kick {TARGET} with PID {found} via bridge_server.py")
    print("Use ?kick 1320454366 in Discord now")
else:
    print("Failed to get PID - need MiniGameApp running")
