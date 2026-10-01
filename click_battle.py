import subprocess
import time
import re

WAYDROID_IP = "192.168.240.112:5555"

def run_adb(cmd):
    """Executes an ADB command and returns string output."""
    full_cmd = ["adb", "-s", WAYDROID_IP] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.stdout.strip()

def get_screen_size():
    """Queries Waydroid's screen resolution (width, height)."""
    output = run_adb(["shell", "wm", "size"])
    match = re.search(r"Physical size:\s*(\d+)x(\d+)", output)
    if match:
        return int(match.group(1)), int(match.group(2))
    # Fallback to standard 1080x1920 if query fails
    return 1080, 1920

def tap_screen(x, y):
    """Executes a touch event at coordinates (x, y)."""
    print(f"[+] Tapping coordinates: ({x}, {y})")
    run_adb(["shell", "input", "tap", str(x), str(y)])

def click_battle_button():
    width, height = get_screen_size()
    print(f"[+] Waydroid Screen Resolution: {width}x{height}")

    # Yellow Battle button is centered horizontally (~50%)
    # and located in the lower-middle section (~78% height)
    target_x = int(width * 0.50)
    target_y = int(height * 0.78)

    print(f"[+] Target Battle Button at ({target_x}, {target_y})")
    tap_screen(target_x, target_y)

if __name__ == "__main__":
    click_battle_button()
