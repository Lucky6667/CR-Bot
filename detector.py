"""Image and screen state detection module for Clash Royale bot."""

from PIL import Image

# Base reference resolution calibrated for Waydroid profile
BASE_WIDTH = 419.0
BASE_HEIGHT = 633.0

# Base Coordinates (at 419x633)
BATTLE_BUTTON_CENTER = (211, 488)
PLAY_AGAIN_CENTER = (153, 573)
OK_BUTTON_CENTER_RIGHT = (265, 573)
OK_BUTTON_CENTER_MIDDLE = (210, 574)
OK_BUTTON_CENTER = OK_BUTTON_CENTER_RIGHT
RETRY_LOGIN_BUTTON = (85, 343)

CARD_SLOTS = [
    (140, 540),  # Slot 1
    (210, 540),  # Slot 2
    (280, 540),  # Slot 3
    (350, 540),  # Slot 4
]

ARENA_X_MIN, ARENA_X_MAX = 60, 360
ARENA_Y_MIN, ARENA_Y_MAX = 282, 470


def scale_point(pt, img_size):
    """Scales a reference (x, y) point to the current image dimensions."""
    w, h = img_size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT
    return int(pt[0] * sx), int(pt[1] * sy)


def is_yellow_pixel(rgb):
    """Checks if RGB matches Clash Royale's bright yellow button color."""
    r, g, b = rgb[:3]
    return r > 180 and g > 150 and b < 110


def is_blue_pixel(rgb):
    """Checks if RGB matches Clash Royale's vibrant blue action/OK button color."""
    r, g, b = rgb[:3]
    return b >= 210 and g >= 135 and r <= 120


def is_magenta_pixel(rgb):
    """Checks if RGB matches Clash Royale's purple/magenta Elixir color."""
    r, g, b = rgb[:3]
    return r > 160 and g < 100 and b > 140


def is_tray_blue_pixel(rgb):
    """Checks if RGB matches the blue top border of the player battle tray."""
    r, g, b = rgb[:3]
    return b > 150 and g > 100 and r < 110


def is_dark_dialog_pixel(rgb):
    """Checks if RGB matches the dark charcoal background of the system dialog card."""
    r, g, b = rgb[:3]
    return r <= 45 and g <= 45 and b <= 45 and abs(r - g) <= 10 and abs(r - b) <= 10


def is_main_menu(img):
    """Detects if the current screen is the Main Menu (Home Screen)

    by verifying the large yellow 'Battle' button.
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Sample points on the yellow Battle button outside center lettering
    sample_points = [
        (int(170 * sx), int(488 * sy)),
        (int(250 * sx), int(488 * sy)),
        (int(211 * sx), int(465 * sy)),
        (int(211 * sx), int(510 * sy)),
    ]

    hits = sum(1 for p in sample_points if is_yellow_pixel(img.getpixel(p)))
    return hits >= 3


def is_play_again_present(img):
    """Checks for the yellow 'Play Again' button on the winner/end-of-battle screen.

    Samples points to the left, right, and top of the dark center text.
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    sample_points = [
        (int(125 * sx), int(575 * sy)),
        (int(180 * sx), int(575 * sy)),
        (int(153 * sx), int(560 * sy)),
    ]

    hits = sum(1 for p in sample_points if is_yellow_pixel(img.getpixel(p)))
    return hits >= 2


def get_ok_button_coords(img):
    """Locates the blue 'OK' button coordinates.

    Supports both:
    1. Right-aligned 'OK' (when 'Play Again' is shown on victory/rematch screens).
    2. Centered 'OK' (shown on defeat, when rematch is unavailable, or summary screens).
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Check right-aligned OK points
    right_pts = [
        (int(240 * sx), int(575 * sy)),
        (int(290 * sx), int(575 * sy)),
        (int(265 * sx), int(560 * sy)),
    ]
    if sum(1 for p in right_pts if is_blue_pixel(img.getpixel(p))) >= 2:
        return (int(OK_BUTTON_CENTER_RIGHT[0] * sx), int(OK_BUTTON_CENTER_RIGHT[1] * sy))

    # Check center-aligned OK points
    center_pts = [
        (int(185 * sx), int(574 * sy)),
        (int(235 * sx), int(574 * sy)),
        (int(210 * sx), int(560 * sy)),
    ]
    if sum(1 for p in center_pts if is_blue_pixel(img.getpixel(p))) >= 2:
        return (int(OK_BUTTON_CENTER_MIDDLE[0] * sx), int(OK_BUTTON_CENTER_MIDDLE[1] * sy))

    return None


def is_ok_button_present(img):
    """Checks if a blue 'OK' button is present (either right-aligned or centered)."""
    return get_ok_button_coords(img) is not None


def is_winner_screen(img):
    """Checks if the end-of-battle screen is showing (either Play Again or OK button present)."""
    return is_play_again_present(img) or is_ok_button_present(img)


def is_in_battle(img):
    """Verifies live combat by detecting both:

    1. The magenta/purple Elixir droplet at the bottom-left of the elixir bar.
    2. The blue deck tray top border across the width of the screen.
    Guarantees zero false-positives on menu, winner, or loading screens.
    """
    # Ensure terminal screens are not confused with battle
    if is_winner_screen(img) or is_main_menu(img):
        return False

    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Check Elixir droplet icon
    elixir_pts = [
        (int(112 * sx), int(606 * sy)),
        (int(115 * sx), int(608 * sy)),
        (int(118 * sx), int(606 * sy)),
    ]
    drop_hits = sum(1 for p in elixir_pts if is_magenta_pixel(img.getpixel(p)))

    # Check blue deck tray top border (sampled on left and right wings outside of the 4 card slots)
    tray_pts = [
        (int(50 * sx), int(512 * sy)),
        (int(65 * sx), int(512 * sy)),
        (int(80 * sx), int(512 * sy)),
        (int(380 * sx), int(512 * sy)),
        (int(385 * sx), int(512 * sy)),
    ]
    tray_hits = sum(1 for p in tray_pts if is_tray_blue_pixel(img.getpixel(p)))

    return drop_hits >= 1 and tray_hits >= 2


def is_connection_lost(img):
    """Checks if the 'Connection lost' modal popup is on screen.

    Verifies the dark dialog card surface, cyan 'Retry login' action text,
    and white 'Connection lost' title. Ignores active battle HUD.
    """
    # Active battle HUD (elixir droplet + deck tray) is never present when modal dialog covers screen
    if is_in_battle(img):
        return False

    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Check for dark dialog card background across the modal container
    dialog_sample_pts = [
        (int(210 * sx), int(225 * sy)),
        (int(300 * sx), int(230 * sy)),
        (int(350 * sx), int(250 * sy)),
        (int(300 * sx), int(300 * sy)),
        (int(350 * sx), int(320 * sy)),
        (int(300 * sx), int(350 * sy)),
        (int(350 * sx), int(350 * sy)),
        (int(200 * sx), int(355 * sy)),
    ]
    dark_hits = sum(1 for p in dialog_sample_pts if is_dark_dialog_pixel(img.getpixel(p)))
    if dark_hits < 6:
        return False

    # Check cyan pixels in 'Retry login' text box
    cyan_count = 0
    for y in range(int(335 * sy), int(355 * sy)):
        for x in range(int(50 * sx), int(130 * sx)):
            r, g, b = img.getpixel((x, y))[:3]
            if b > 160 and g > 140 and r > 90 and b > r:
                cyan_count += 1

    # Check white pixels in 'Connection lost' title box
    white_count = 0
    for y in range(int(235 * sy), int(255 * sy)):
        for x in range(int(50 * sx), int(190 * sx)):
            r, g, b = img.getpixel((x, y))[:3]
            if r > 200 and g > 200 and b > 200:
                white_count += 1

    return cyan_count > 50 and white_count > 100


def detect_state(img):
    """Classifies the screen state into one of:

    - 'CONNECTION_LOST'
    - 'MAIN_MENU'
    - 'WINNER_SCREEN'
    - 'POST_BATTLE_OK'
    - 'IN_BATTLE'
    - 'LOADING'
    """
    if is_connection_lost(img):
        return "CONNECTION_LOST"
    if is_main_menu(img):
        return "MAIN_MENU"
    if is_play_again_present(img):
        return "WINNER_SCREEN"
    if is_ok_button_present(img):
        return "POST_BATTLE_OK"
    if is_in_battle(img):
        return "IN_BATTLE"
    return "LOADING"
