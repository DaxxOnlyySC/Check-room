"""Try to get PID from MiniGameApp.exe even without window, then gm.kick"""
import psutil, subprocess, time, os

TARGET = "1320454366"
EXE = r"C:\Users\daxxx\AppData\Roaming\miniworldOverseasgame\MiniGameApp.exe"

print("Checking MiniGameApp PID...")
EXE2 = r"C:\Users\daxxx\AppData\Roaming\miniworldOverseasgame\MicroMiniNew.exe"
found = None
for p in psutil.process_iter(['pid','name']):
    if p.info['name'].lower() == 'minigameapp.exe':
        found = p.info['pid']
        break
if found:
    print(f"Found MiniGameApp PID {found}")
else:
    for p in psutil.process_iter(['pid','name']):
        if p.info['name'].lower() == 'micromininew.exe':
            found = p.info['pid']
            print(f"Found MicroMiniNew PID {found} (MiniGameApp not yet)")
            break
if found:
    print(f"Can gm.kick {TARGET} via bridge")
else:
    print("No PID - try MicroMiniNew hidden...")
    try:
        subprocess.Popen([EXE2], creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(10)
        for p in psutil.process_iter(['pid','name']):
            if p.info['name'].lower() == 'minigameapp.exe':
                print(f"Started MiniGameApp PID {p.info['pid']} via MicroMiniNew")
                found = p.info['pid']
                break
            if p.info['name'].lower() == 'micromininew.exe':
                print(f"Started MicroMiniNew PID {p.info['pid']}")
                found = p.info['pid']
                break
    except Exception as e:
        print(f"start err {e}")

if found:
    print(f"Ready to gm.kick {TARGET} with PID {found} via bridge_server.py")
    print("Use ?kick 1320454366 in Discord now")
else:
    print("Failed to get PID - need MiniGameApp running")
