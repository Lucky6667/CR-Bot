import os
import subprocess
from PIL import Image
import detector

WAYDROID_IP = "192.168.240.112:5555"
REMOTE_PATH = "/sdcard/screen.png"
LOCAL_PATH = "screen.png"


def capture_live_screen():
  """Pull live screenshot from Waydroid if available."""
  try:
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
    return LOCAL_PATH
  except Exception as e:
    print(f"[!] Could not pull live screenshot via ADB: {e}")
    return None


def test_winner_detection(image_path):
  if not os.path.exists(image_path):
    print(f"[FAIL] Target image file '{image_path}' not found.")
    return

  img = Image.open(image_path)
  width, height = img.size
  print(f"[+] Loaded image: '{image_path}' ({width}x{height})")

  state = detector.detect_state(img)
  has_play_again = detector.is_play_again_present(img)
  ok_coords = detector.get_ok_button_coords(img)

  print(f"[+] 'Play Again' button (Yellow): {has_play_again}")
  print(f"[+] 'OK' button (Blue):          {ok_coords is not None} -> Target: {ok_coords}")
  print(f"[+] Classified Screen State:     '{state}'")

  if has_play_again and ok_coords:
    print("\n[OK] DETECTED: Rematch screen with both 'Play Again' and 'OK' buttons!")
  elif has_play_again:
    print("\n[OK] DETECTED: 'Play Again' yellow button active!")
  elif ok_coords:
    print(f"\n[OK] DETECTED: Match end / Defeat / Summary screen with 'OK' button at {ok_coords}!")
  else:
    print("\n[-] NOT DETECTED: End-of-battle buttons not found.")


if __name__ == "__main__":
  # Prioritize stuck_screen.png if present, then test_winner.png, then live capture
  target = None
  for candidate in ["stuck_screen.png", "test_winner.png"]:
    if os.path.exists(candidate):
      target = candidate
      break

  if target:
    test_winner_detection(target)
  else:
    live_img = capture_live_screen()
    if live_img:
      test_winner_detection(live_img)
