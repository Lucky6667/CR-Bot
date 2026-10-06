"""CR-Bot: Automated Clash Royale Bot for Waydroid.

Features:
- Robust multi-screen state classification (Home, Challenges, Winner, Defeat, Connection Lost, Event Roadmaps).
- Event screen & reward roadmap auto-dismissal via blue 'Close' button detection.
- Challenge / Event mode support with green "FREE!" retry detection and gem-cost safeguards.
- Strategic lane management and tactical deployment zones (inspired by py-clash-bot).
- Card affordability verification via elixir badge detection (avoids dead taps).
- Real-time elixir gauge monitoring (fast-cycles when full, paces recharge).
- Automatic Hero / Champion ability triggering.
- Optional in-game emote interactions.
- Automatic ADB reconnection and self-healing.
"""

from collections import deque
import os
import random
import subprocess
import sys
import time
from PIL import Image
import detector
import tactics

# Ensure stdout and stderr handle any terminal locale safely without encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="backslashreplace")

WAYDROID_IP = "192.168.240.112:5555"
REMOTE_PATH = "/sdcard/screen.png"
LOCAL_PATH = "screen.png"
CLASH_PACKAGE = "com.supercell.clashroyale/com.supercell.titan.GameApp"


def run_adb(cmd):
    """Executes an ADB command with automatic reconnection."""
    full_cmd = ["adb", "-s", WAYDROID_IP] + cmd
    res = subprocess.run(full_cmd, capture_output=True)
    if res.returncode != 0:
        ensure_adb_connected()
        subprocess.run(full_cmd, capture_output=True)


def ensure_adb_connected():
    """Verifies connection to Waydroid, reconnecting if dropped."""
    check = subprocess.run(["adb", "-s", WAYDROID_IP, "get-state"], capture_output=True, text=True)
    if "device" not in check.stdout:
        print(f"[!] Reconnecting ADB to Waydroid at {WAYDROID_IP}...")
        subprocess.run(["adb", "connect", WAYDROID_IP], capture_output=True)
        time.sleep(1.5)


def tap(x, y):
    """Executes a touch event on Waydroid."""
    run_adb(["shell", "input", "tap", str(x), str(y)])


def capture_screen():
    """Captures screenshot cleanly via file pull to bypass driver log pollution."""
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
        return Image.open(LOCAL_PATH)
    except Exception as e:
        ensure_adb_connected()
        time.sleep(1.0)
        return Image.open(LOCAL_PATH)


def run_bot():
    print("=" * 60)
    print("     CR-BOT: TACTICAL CLASH ROYALE BOT FOR WAYDROID")
    print("=" * 60)
    print("[+] Waydroid Target IP:", WAYDROID_IP)
    print("[+] Press Ctrl+C to stop the bot.\n")

    ensure_adb_connected()
    tactics_engine = tactics.BattleTactics()
    matches_started = 0
    start_time = time.time()

    try:
        while True:
            img = capture_screen()
            state = detector.detect_state(img)
            w, h = img.size

            # 0. CONNECTION LOST: Tap 'Retry login'
            if state == "CONNECTION_LOST":
                rx, ry = detector.scale_point(detector.RETRY_LOGIN_BUTTON, (w, h))
                print(f"[!] Connection lost modal detected! Tapping 'Retry login' at ({rx}, {ry})...")
                tap(rx, ry)
                time.sleep(4.0)

            # 1. MAIN MENU / CHALLENGE LOBBY: Initiate Battle
            elif state == "MAIN_MENU":
                tactics_engine.reset_match()
                bx, by = detector.scale_point(detector.BATTLE_BUTTON_CENTER, (w, h))
                matches_started += 1
                print(f"[!] Match Ready! Initiating Battle #{matches_started} at ({bx}, {by})...")
                tap(bx, by)
                print("[+] Matchmaking triggered. Waiting for arena to load...\n")

                for _ in range(20):
                    time.sleep(1)
                    match_img = capture_screen()
                    match_state = detector.detect_state(match_img)
                    if match_state == "IN_BATTLE":
                        print(f"[OK] Match #{matches_started} loaded! Entering tactical battle loop.\n")
                        break

            # 1b. GREEN FREE BUTTON: Continue / Enter for Free
            elif state == "GREEN_FREE_BUTTON":
                tactics_engine.reset_match()
                bx, by = detector.scale_point(detector.BATTLE_BUTTON_CENTER, (w, h))
                print(f"[!] Green 'FREE!' button detected! Initiating free continuation/entry at ({bx}, {by})...")
                tap(bx, by)
                print("[+] Free button tapped. Waiting for screen to update...\n")
                time.sleep(2.5)

            # 1c. GREEN PAID BUTTON: Stop if button is NOT 'FREE!' to protect gems
            elif state == "GREEN_PAID_BUTTON":
                print("\n[!] WARNING: Action button requires Gems or paid entry (does not say 'FREE!').")
                print("[!] Halting battle loop to preserve Gems/resources as requested.\n")
                break

            # 2. WINNER SCREEN: Rematch via 'Play Again'
            elif state == "WINNER_SCREEN":
                tactics_engine.reset_match()
                pax, pay = detector.scale_point(detector.PLAY_AGAIN_CENTER, (w, h))
                print(f"[!] Winner screen detected! Tapping 'Play Again' at ({pax}, {pay})...")
                tap(pax, pay)
                time.sleep(3.0)

            # 3. POST-MATCH SUMMARY / REWARDS: Dismiss via 'OK'
            elif state == "POST_BATTLE_OK":
                ok_coords = detector.get_ok_button_coords(img)
                if ok_coords:
                    okx, oky = ok_coords
                else:
                    okx, oky = detector.scale_point(detector.OK_BUTTON_CENTER_MIDDLE, (w, h))
                print(f"[!] Summary/Rewards screen detected! Tapping OK at ({okx}, {oky})...")
                tap(okx, oky)
                time.sleep(2.0)

            # 3b. EVENT / ROADMAP SCREEN: Dismiss via 'Close'
            elif state == "EVENT_SCREEN":
                tactics_engine.reset_match()
                close_coords = detector.get_close_button_coords(img)
                if close_coords:
                    cx, cy = close_coords
                else:
                    cx, cy = detector.scale_point(detector.CLOSE_BUTTON_CENTER, (w, h))
                print(f"[!] Event screen detected! Tapping 'Close' at ({cx}, {cy})...")
                tap(cx, cy)
                time.sleep(2.0)

            # 4. ACTIVE BATTLE: Tactical card play, elixir tracking, abilities & emotes
            elif state == "IN_BATTLE":
                # A. Hero / Champion ability trigger
                if tactics.is_champion_ability_available(img):
                    ax, ay = detector.scale_point(tactics.CHAMPION_ABILITY_TRIGGER_COORD, (w, h))
                    print(f"[*] Champion Ability Ready! Triggering ability at ({ax}, {ay})...")
                    tap(ax, ay)
                    tactics_engine.abilities_used += 1
                    time.sleep(0.2)

                # B. In-battle emote
                if tactics_engine.should_send_emote():
                    ex, ey = detector.scale_point(tactics.EMOTE_BUTTON_COORD, (w, h))
                    tap(ex, ey)
                    time.sleep(0.2)
                    emote_pt = random.choice(tactics.EMOTE_ICON_COORDS)
                    emx, emy = detector.scale_point(emote_pt, (w, h))
                    tap(emx, emy)
                    tactics_engine.emotes_sent += 1
                    print("[EMOTE] Sent battle emote!")

                # C. Elixir & Card Hand analysis
                elixir = tactics.count_elixir(img)
                available_slots = tactics.get_available_card_indices(img)

                # Deploy if cards are affordable or elixir is high
                if available_slots or elixir >= 5:
                    slot_idx = tactics_engine.select_card_slot(available_slots)
                    raw_slot = detector.CARD_SLOTS[slot_idx]
                    slot_x, slot_y = detector.scale_point(raw_slot, (w, h))

                    target_raw, play_desc = tactics_engine.plan_tactical_play(img, elixir=elixir)
                    target_x, target_y = detector.scale_point(target_raw, (w, h))

                    ready_desc = f"{len(available_slots)}/4 ready" if available_slots else "cycle tap"
                    print(f"[+] [{play_desc}] Slot {slot_idx+1} -> ({target_x}, {target_y}) (Elixir: {elixir}/10 | {ready_desc})")
                    tap(slot_x, slot_y)
                    time.sleep(0.12)
                    tap(target_x, target_y)

                    # Dynamic pacing: fast-cycle when elixir is overflowing, otherwise wait for recharge
                    if elixir >= 9:
                        cooldown = random.uniform(1.2, 1.8)
                        print(f"[FAST] High Elixir ({elixir}/10)! Fast-cycling in {cooldown:.1f}s...\n")
                    else:
                        cooldown = random.uniform(2.2, 3.4)
                        print(f"[~] Waiting {cooldown:.1f}s for elixir recharge (current: {elixir}/10)...\n")
                    time.sleep(cooldown)
                else:
                    print(f"[WAIT] Elixir charging ({elixir}/10, no cards ready). Waiting 1.0s...")
                    time.sleep(1.0)

            # 5. TRANSITION / LOADING
            else:
                # Tap safe neutral deadspace to dismiss lingering tooltip bubbles
                dx, dy = detector.scale_point(tactics.DEADSPACE_COORD, (w, h))
                tap(dx, dy)
                print("[...] Transitioning or loading. Waiting...")
                time.sleep(1.5)

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        print("\n" + "=" * 60)
        print("                 CR-BOT SESSION SUMMARY")
        print("=" * 60)
        print(f"[+] Runtime:            {mins}m {secs}s")
        print(f"[+] Matches Started:    {matches_started}")
        print(f"[+] Cards Deployed:     {tactics_engine.cards_played}")
        print(f"[+] Abilities Used:     {tactics_engine.abilities_used}")
        print(f"[+] Emotes Sent:        {tactics_engine.emotes_sent}")
        print("=" * 60)
        print("[!] CR-Bot stopped by user.")


if __name__ == "__main__":
    run_bot()
