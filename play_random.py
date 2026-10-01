import subprocess
import time
import random
from PIL import Image
import detector

WAYDROID_IP = "192.168.240.112:5555"
REMOTE_PATH = "/sdcard/screen.png"
LOCAL_PATH = "screen.png"


def run_adb(cmd):
    full_cmd = ["adb", "-s", WAYDROID_IP] + cmd
    subprocess.run(full_cmd, capture_output=True)


def tap(x, y):
    run_adb(["shell", "input", "tap", str(x), str(y)])


def capture_screen():
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


def play_random_card(img_size=(419, 633)):
    raw_slot = random.choice(detector.CARD_SLOTS)
    slot_x, slot_y = detector.scale_point(raw_slot, img_size)

    raw_x = random.randint(detector.ARENA_X_MIN, detector.ARENA_X_MAX)
    raw_y = random.randint(detector.ARENA_Y_MIN, detector.ARENA_Y_MAX)
    target_x, target_y = detector.scale_point((raw_x, raw_y), img_size)

    print(f"[+] Selecting card slot at ({slot_x}, {slot_y})...")
    tap(slot_x, slot_y)
    time.sleep(0.15)

    print(f"[+] Deploying unit to arena at ({target_x}, {target_y})...")
    tap(target_x, target_y)


def bot_loop():
    print("[+] Starting Paced CR-Bot Loop...")
    print("[+] Press Ctrl+C to stop.\n")

    try:
        while True:
            img = capture_screen()
            state = detector.detect_state(img)
            w, h = img.size

            if state == "CONNECTION_LOST":
                rx, ry = detector.scale_point(detector.RETRY_LOGIN_BUTTON, (w, h))
                print(f"[!] Connection lost modal detected! Tapping 'Retry login' at ({rx}, {ry})...")
                tap(rx, ry)
                time.sleep(4.0)

            elif state == "IN_BATTLE":
                play_random_card(img_size=(w, h))
                cooldown = random.uniform(2.2, 3.8)
                print(f"[~] Waiting {cooldown:.1f}s for elixir...")
                time.sleep(cooldown)

            elif state == "MAIN_MENU":
                bx, by = detector.scale_point(detector.BATTLE_BUTTON_CENTER, (w, h))
                print(f"[!] Main Menu detected. Tapping Battle button at ({bx}, {by})...")
                tap(bx, by)
                print("[+] Waiting for match load...")

                for _ in range(15):
                    time.sleep(1)
                    match_img = capture_screen()
                    if detector.is_in_battle(match_img):
                        print("[OK] Match loaded!")
                        break

            elif state == "WINNER_SCREEN":
                pax, pay = detector.scale_point(detector.PLAY_AGAIN_CENTER, (w, h))
                print(f"[!] Winner screen detected. Tapping 'Play Again' at ({pax}, {pay})...")
                tap(pax, pay)
                time.sleep(3.0)

            elif state == "POST_BATTLE_OK":
                ok_coords = detector.get_ok_button_coords(img)
                if ok_coords:
                    okx, oky = ok_coords
                else:
                    okx, oky = detector.scale_point(detector.OK_BUTTON_CENTER_MIDDLE, (w, h))
                print(f"[!] OK button detected. Tapping OK at ({okx}, {oky})...")
                tap(okx, oky)
                time.sleep(2.0)

            else:
                print("[...] Loading screen or transitioning. Waiting...")
                time.sleep(1.5)

    except KeyboardInterrupt:
        print("\n[!] Bot loop stopped by user.")


if __name__ == "__main__":
    bot_loop()
