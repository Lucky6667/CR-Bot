import subprocess
import os
from PIL import Image

WAYDROID_IP = "192.168.240.112:5555"
REMOTE_PATH = "/sdcard/test.png"
LOCAL_PATH = "test_grab.png"

def capture_test_image():
    print(f"[+] Capturing screenshot inside Waydroid ({REMOTE_PATH})...")
    # Save directly inside Android storage to avoid stdout log corruption
    subprocess.run(["adb", "-s", WAYDROID_IP, "shell", "screencap", "-p", REMOTE_PATH], check=True)

    print(f"[+] Pulling image to local disk ({LOCAL_PATH})...")
    subprocess.run(["adb", "-s", WAYDROID_IP, "pull", REMOTE_PATH, LOCAL_PATH], check=True, capture_output=True)

    if os.path.exists(LOCAL_PATH):
        img = Image.open(LOCAL_PATH)
        print("[OK] Screenshot captured successfully!")
        print(f"     Saved file : {LOCAL_PATH}")
        print(f"     Dimensions : {img.size[0]}x{img.size[1]} (Width x Height)")
        print(f"     Color Mode : {img.mode}")
        return True
    else:
        print("[FAIL] Could not retrieve screenshot file.")
        return False

if __name__ == "__main__":
    capture_test_image()
