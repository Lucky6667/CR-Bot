# CR-Bot: Automated Clash Royale Bot for Waydroid

An automated Clash Royale bot designed to run with Waydroid via ADB. Features robust image state detection, automatic matchmaking, active combat card deployment, and match-end screen navigation.

## Features

- **Automated Battle Lifecycle**: Initiates battles from the main menu, plays cards during combat, and navigates post-battle screens.
- **Robust Screen State Detection (`detector.py`)**:
  - **Main Menu & Challenge Lobby**: Yellow Battle button detection with multi-point verification across varied arena color schemes.
  - **Challenge / Event Continuation (`FREE!`)**: Vectorized template matching to detect the green "FREE!" retry/continuation button, with automatic safeguards that halt the bot if a paid button (e.g. Gem cost) appears.
  - **Live Combat**: Magenta elixir droplet and blue deck tray border detection (zero false positives).
  - **Rematch Navigation**: Detects yellow "Play Again" and blue "OK" buttons on victory.
  - **Defeat & Dialog Handling**: Automatically detects and taps centered blue "OK" buttons on defeat or summary popups.
  - **Event Screen / Roadmap Dismissal**: Detects progress roadmaps and modal event screens (e.g. "Watts of Rewards!") via template and pixel matching on the blue "Close" button, automatically resuming the match loop.
- **Tactical Combat Intelligence (`tactics.py`)** (inspired by `py-clash-bot` & `ClashRoyaleBuildABot`):
  - **Dynamic Tower Health Evaluation**: Continuously tracks enemy Princess Tower HP bars in real-time, automatically prioritizing and concentrating offensive pushes on the weaker enemy tower.
  - **Defensive Incursion Detection & Center Pull Counters**: Continuously scans friendly territory (`y: 285..440`) for enemy troop health bars; executes a classic 4-3 center pull (`defense_center`) to lure attackers between both Princess Towers when threatened.
  - **Pocket Rush Aggression**: Dynamically detects when an enemy Princess Tower is destroyed, unlocking immediate pocket deployments (`pocket_rush`) into enemy territory for high-tempo tower punish.
  - **Tile Grid Mapping System**: Provides full conversion between standard Clash Royale 18x32 tile coordinates (`tile_to_base_coords`) and device screen space.
  - **Dual-Mode Card Readiness Detection**: Combines color channel standard deviation saturation analysis (`_detect_if_ready`) with magenta cost badge verification for 100% card playability detection.
  - **Strategic Lane & Placement Zones**: Coordinated lane pushes (`left` / `right`) targeting calibrated zones (`bridge_rush`, `back_support`, `king_lane`, `defense_center`, `pocket_rush`).
  - **Adaptive Elixir-Driven Tactics**: Fast-cycles bridge rushes at high elixir (>= 8-10) and plays back-support/king-lane deployments at moderate elixir to build unstoppable beatdown pushes.
  - **Card Deck Cycling Queue**: Tracks recent cards via a deque to prevent repetitive spam-locking and promote healthy card rotation.
  - **Champion & Hero Abilities**: Automatically detects and activates Hero abilities when ready.
  - **In-Game Emotes**: Periodic emote triggers with human-like randomness and organic placement jitter.
  - **Deadspace Tap**: Neutral taps to safely dismiss transient bubbles and floating rewards.
- **Resolution Scaling**: Automatically scales reference coordinates across different display resolutions.

## Requirements

- Python 3.8+
- [Pillow](https://python-pillow.org/) (`pip install pillow`)
- [NumPy](https://numpy.org/) (`pip install numpy`)
- [Waydroid](https://waydro.id/) with Clash Royale installed
- Android Debug Bridge (`adb`)

## Quick Start

1. **Connect ADB to Waydroid**:
   ```bash
   python3 launch.py
   ```
2. **Start the Bot**:
   ```bash
   python3 main_bot.py
   ```

## Project Structure

- `main_bot.py` - Core bot loop with integrated state machine and tactical deployment.
- `tactics.py` - Advanced battle strategy, placement zones, elixir reading, and hero abilities.
- `detector.py` - Screen state classifier, template matching, and coordinate scaling module.
- `battle_detector.py` - Standalone battle button detection.
- `play_random.py` - Alternative paced random card deployment loop.
- `launch.py` - Helper script to connect ADB and launch Clash Royale.
- `test_winner_check.py` - Diagnostic tool to verify end-of-battle detection.
