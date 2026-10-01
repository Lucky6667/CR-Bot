import subprocess
import io
import time
from PIL import Image

WAYDROID_IP = "192.168.240.112:5555"

def run_adb(cmd):
    full_cmd = ["adb", "-s", WAYDROID_IP] + cmd
    subprocess.run(full_cmd, capture_output=True)

def get_screenshot():
    cmd = ["adb", "-s", WAYDROID_IP, "exec-out", "screencap", "-p"]
    png_bytes = subprocess.check_output(cmd)
    
    png_header_index = png_bytes.find(b"\x89PNG")
    if png_header_index == -1:
        print(f"[FAIL] Received non-PNG data from ADB: {png_bytes[:100]}")
        raise ValueError("Invalid image stream received from ADB")
    
    png_bytes = png_bytes[png_header_index:].replace(b"\r\n", b"\n")
    return Image.open(io.BytesIO(png_bytes))

def tap(x, y):
    run_adb(["shell", "input", "tap", str(x), str(y)])

if __name__ == "__main__":
    print("[+] Capturing test frame...")
    img = get_screenshot()
    print(f"[OK] Captured frame with size: {img.size}")
