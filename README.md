# CR-Bot: Automated Clash Royale Bot for Waydroid

An automated Clash Royale bot designed to run with Waydroid via ADB. Features robust image state detection, automatic matchmaking, active combat card deployment, and match-end screen navigation.

## Features

- **Automated Battle Lifecycle**: Initiates battles from the main menu, plays cards during combat, and navigates post-battle screens.
- **Robust Screen State Detection (`detector.py`)**:
  - **Main Menu**: Yellow Battle button detection with multi-point verification.
  - **Live Combat**: Magenta elixir droplet and blue deck tray border detection (zero false positives).
  - **Rematch Navigation**: Detects yellow "Play Again" and blue "OK" buttons on victory.
  - **Defeat & Dialog Handling**: Automatically detects and taps centered blue "OK" buttons on defeat or summary popups.
  - **Connection Lost Recovery**: Identifies "Connection lost" modal popups and taps "Retry login" to reconnect.
- **Resolution Scaling**: Automatically scales reference coordinates across different display resolutions.

## Requirements

- Python 3.8+
- [Pillow](https://python-pillow.org/) (`pip install pillow`)
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

- `main_bot.py` - Core bot loop with integrated state machine.
- `detector.py` - Screen state classifier and coordinate scaling module.
- `battle_detector.py` - Standalone battle button detection.
- `play_random.py` - Alternative paced random card deployment loop.
- `launch.py` - Helper script to connect ADB and launch Clash Royale.
- `test_winner_check.py` - Diagnostic tool to verify end-of-battle detection.
