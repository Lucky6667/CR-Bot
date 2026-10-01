import subprocess
import time

WAYDROID_IP = "192.168.240.112:5555"
ACTIVITY = "com.supercell.clashroyale/com.supercell.titan.GameApp"

def run_adb(cmd):
    """Executes an ADB command and returns output."""
    full_cmd = ["adb", "-s", WAYDROID_IP] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.stdout.strip()

def connect_waydroid():
    print(f"[+] Connecting ADB to Waydroid at {WAYDROID_IP}...")
    subprocess.run(["adb", "connect", WAYDROID_IP], capture_output=True)

    state = run_adb(["get-state"])
    if "device" in state:
        print("[OK] Successfully connected to Waydroid!")
        return True
    else:
        print(f"[FAIL] Failed to connect. State: {state}")
        return False

def launch_clash_royale():
    print(f"[+] Launching Clash Royale ({ACTIVITY})...")
    run_adb(["shell", "am", "start", "-n", ACTIVITY])
    time.sleep(3)

    ps_out = run_adb(["shell", "pidof", "com.supercell.clashroyale"])
    if ps_out:
        print(f"[OK] Clash Royale process active with PID: {ps_out}")
    else:
        print("[FAIL] Process did not start.")

if __name__ == "__main__":
    if connect_waydroid():
        launch_clash_royale()
