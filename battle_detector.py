import subprocess
import os
import time
from PIL import Image
import detector

WAYDROID_IP = "192.168.240.112:5555"
REMOTE_PATH = "/sdcard/screen.png"
LOCAL_PATH = "screen.png"


def run_adb(cmd):
  """Executes an ADB command."""
  full_cmd = ["adb", "-s", WAYDROID_IP] + cmd
  result = subprocess.run(full_cmd, capture_output=True, text=True)
  return result.stdout.strip()


def capture_screen():
  """Captures screenshot safely via file pull to bypass log pollution."""
  subprocess.run(
      ["adb", "-s", WAYDROID_IP, "shell", "screencap", "-p", REMOTE_PATH],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  subprocess.run(
      ["adb", "-s", WAYDROID_IP, "pull", REMOTE_PATH, LOCAL_PATH],
      check=True,
      capture_output=True,
  )
  return Image.open(LOCAL_PATH)


def is_battle_button_viable(img):
  """Detects if the Battle button is present on the screen."""
  return detector.is_main_menu(img)


def click_battle_if_viable():
  print("[+] Capturing screen to check for Battle button...")
  img = capture_screen()

  if is_battle_button_viable(img):
    bx, by = detector.scale_point(detector.BATTLE_BUTTON_CENTER, img.size)
    print(f"[OK] Yellow Battle button detected at ({bx}, {by})!")
    print(f"[+] Tapping ({bx}, {by})...")
    run_adb(["shell", "input", "tap", str(bx), str(by)])
    return True
  else:
    print("[-] Battle button is NOT viable (not on main menu or covered).")
    return False


if __name__ == "__main__":
  click_battle_if_viable()
