@echo off
echo === Headless Gate 24/7 - UIN Keepalive ===
set HEADLESS_UIN=1321663876
set HEADLESS_DEVICE_ID=WIN6764fc68c5f9929bc7e572da64e71ef8
REM Uncomment kalau butuh PW pertama kali:
REM set HEADLESS_PW=TheDark12345#

python headless_gate.py
pause
