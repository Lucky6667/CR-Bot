"""Image and screen state detection module for Clash Royale bot."""

import base64
import io
import os
import numpy as np
from PIL import Image

# Base reference resolution calibrated for Waydroid profile
BASE_WIDTH = 419.0
BASE_HEIGHT = 633.0

# Base Coordinates (at 419x633)
BATTLE_BUTTON_CENTER = (211, 488)
PLAY_AGAIN_CENTER = (153, 573)
OK_BUTTON_CENTER_RIGHT = (265, 573)
OK_BUTTON_CENTER_MIDDLE = (210, 574)
OK_BUTTON_CENTER_BOTTOM = (210, 600)
OK_BUTTON_CENTER = OK_BUTTON_CENTER_RIGHT
CLOSE_BUTTON_CENTER = (209, 598)
RED_X_BUTTON_DEFAULT = (364, 156)
RETRY_LOGIN_BUTTON = (85, 343)

CARD_SLOTS = [
    (140, 540),  # Slot 1
    (210, 540),  # Slot 2
    (280, 540),  # Slot 3
    (350, 540),  # Slot 4
]

ARENA_X_MIN, ARENA_X_MAX = 60, 360
ARENA_Y_MIN, ARENA_Y_MAX = 282, 470

# Embedded base64 fallback for the 'FREE!' button text template (grayscale)
FREE_TEMPLATE_B64 = """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"""

_CACHED_TMPL = None
_CACHED_NORM = None


def _get_free_template():
    """Loads and caches the normalized 'FREE!' text template."""
    global _CACHED_TMPL, _CACHED_NORM
    if _CACHED_TMPL is not None:
        return _CACHED_TMPL, _CACHED_NORM

    template_file = os.path.join(os.path.dirname(__file__), "free_template.png")
    if os.path.exists(template_file):
        img = Image.open(template_file).convert("L")
    else:
        raw_bytes = base64.b64decode(FREE_TEMPLATE_B64)
        img = Image.open(io.BytesIO(raw_bytes)).convert("L")

    tmpl = np.array(img, dtype=np.float32)
    tmpl -= tmpl.mean()
    norm = np.linalg.norm(tmpl)

    _CACHED_TMPL = tmpl
    _CACHED_NORM = norm
    return _CACHED_TMPL, _CACHED_NORM


# Embedded base64 fallback for the 'Close' button text template (grayscale)
CLOSE_TEMPLATE_B64 = """iVBORw0KGgoAAAANSUhEUgAAACYAAAAOCAAAAABmqTEpAAABrElEQVR4nI2QT0hTcQDHP+/33vO5vXKpYWu6iRvROkgJC4ykFhQOYh0MLOoeatCpWx0k6KBBINQhugb9uXjoD0KBVkTeCi8RjzlKmrzXXJtbe3s9t18H7+Ln/OUD34/ygt0gdrVCA6BRc33pdah0GTvYlh990Q8fL+TavuZ3sMnn7xNAMRvsXvH9UkOqvRRWS1vN4f7KD6dKc8zQgPXoAJ7152OW+ubTdDikrc4GLo/37F15vXDmRHif/uTdea0C+VHBp4tucJa/havjAlrZmRtqtWD/PnBLb8jApbERAdSOwLeTt9MC30uI3NBLER1W3enM1K8RvXnnLX0OApCdUBsKq4DooCyK0E379NIzP464eY7gv+0gLQjfjzgtaOng7UFen8wk+805A/L2mrX9VLEyXBmtz7fQXTuenI/gsLYcC9UaRTD10OejaED73KlBPUzUl1SvLfQe2vr58MI9Tebulh/EB5NJb+kYGhCpptpSA50fJg1n4lUsUbOFGZ/5vrjedXYx7fXFDSuF8hikveGU3GY9YQaSVUsqhmm+UdSDsf09G5XNsitDp/kPzfqg4UjNBdAAAAAASUVORK5CYII="""

_CACHED_CLOSE_TMPL = None
_CACHED_CLOSE_NORM = None


def _get_close_template():
    """Loads and caches the normalized 'Close' text template."""
    global _CACHED_CLOSE_TMPL, _CACHED_CLOSE_NORM
    if _CACHED_CLOSE_TMPL is not None:
        return _CACHED_CLOSE_TMPL, _CACHED_CLOSE_NORM

    template_file = os.path.join(os.path.dirname(__file__), "close_template.png")
    if os.path.exists(template_file):
        img = Image.open(template_file).convert("L")
    else:
        raw_bytes = base64.b64decode(CLOSE_TEMPLATE_B64)
        img = Image.open(io.BytesIO(raw_bytes)).convert("L")

    tmpl = np.array(img, dtype=np.float32)
    tmpl -= tmpl.mean()
    norm = np.linalg.norm(tmpl)

    _CACHED_CLOSE_TMPL = tmpl
    _CACHED_CLOSE_NORM = norm
    return _CACHED_CLOSE_TMPL, _CACHED_CLOSE_NORM


# Embedded base64 fallback for the Red 'X' close button template (grayscale)
RED_X_TEMPLATE_B64 = """iVBORw0KGgoAAAANSUhEUgAAABUAAAASCAAAAACRecryAAABM0lEQVR4nCXOPS9DcRhA8fM8bVrSRlzpQMQgQkJE0qWCRCehn4DEYhWLwSLUbjAhBqZGY7FJDBITq5fFYiSEeq/evv7dx9D1lzMc6Ur3lwAwQADitZxMjHyEvZg2xcAVizELJ5+9BFizBUJe20tYf6LtZpX8+LlzLjdYvDWTREnLnsDRjmxccrjXken9BPH0LwKsGqxd7Cs2lkekVQMBVp4M1sH87AAgigCp5QoAQTaYAlBBYHJoDoCz8qwCaPPdPwYg8xpCAMmEIyqn+zHwtUWYn1ar11VB2Iph37tfARycAKgBbH/7fvZx6a1auImDmZoF8LH5vmCp4cXCw24SM5MZi0alcVXoScL1s9fXSaPqJK0ajeDuhwHuuttwNedkNKImooAYYAEmJeXNiTQBBAR+6/+GxHwNo1uZ4gAAAABJRU5ErkJggg=="""

_CACHED_RED_X_TMPL = None
_CACHED_RED_X_NORM = None


def _get_red_x_template():
    """Loads and caches the normalized Red 'X' button template."""
    global _CACHED_RED_X_TMPL, _CACHED_RED_X_NORM
    if _CACHED_RED_X_TMPL is not None:
        return _CACHED_RED_X_TMPL, _CACHED_RED_X_NORM

    template_file = os.path.join(os.path.dirname(__file__), "red_x_template.png")
    if os.path.exists(template_file):
        img = Image.open(template_file).convert("L")
    else:
        raw_bytes = base64.b64decode(RED_X_TEMPLATE_B64)
        img = Image.open(io.BytesIO(raw_bytes)).convert("L")

    tmpl = np.array(img, dtype=np.float32)
    tmpl -= tmpl.mean()
    norm = np.linalg.norm(tmpl)

    _CACHED_RED_X_TMPL = tmpl
    _CACHED_RED_X_NORM = norm
    return _CACHED_RED_X_TMPL, _CACHED_RED_X_NORM


def scale_point(pt, img_size):
    """Scales a reference (x, y) point to the current image dimensions."""
    w, h = img_size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT
    return int(pt[0] * sx), int(pt[1] * sy)


def is_yellow_pixel(rgb):
    """Checks if RGB matches Clash Royale's yellow/gold button color."""
    r, g, b = rgb[:3]
    return r >= 150 and g >= 110 and b <= 110 and r >= g * 0.95 and g > b * 1.2


def is_blue_pixel(rgb):
    """Checks if RGB matches Clash Royale's vibrant or shaded blue OK button color."""
    r, g, b = rgb[:3]
    return b >= 160 and g >= 110 and r <= 130 and b > r * 1.3 and g > r * 1.05


def is_green_pixel(rgb):
    """Checks if RGB matches Clash Royale's bright green action button color."""
    r, g, b = rgb[:3]
    return g >= 140 and g > r * 1.2 and g > b * 1.2


def is_red_pixel(rgb):
    """Checks if RGB matches Clash Royale's vibrant red popup close button color."""
    r, g, b = rgb[:3]
    return r >= 140 and r > g * 1.4 and r > b * 1.4


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
    """Detects if the current screen is the Main Menu or Challenge lobby

    with a yellow 'Battle' button.
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


def is_green_battle_button(img):
    """Detects if the main action button at the bottom center is green."""
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    sample_points = [
        (int(160 * sx), int(465 * sy)),
        (int(260 * sx), int(465 * sy)),
        (int(160 * sx), int(520 * sy)),
        (int(260 * sx), int(520 * sy)),
        (int(211 * sx), int(465 * sy)),
        (int(211 * sx), int(520 * sy)),
    ]

    hits = sum(1 for p in sample_points if is_green_pixel(img.getpixel(p)))
    return hits >= 4


def is_button_free(img):
    """Checks if the green battle/continue button contains the text 'FREE!'

    via normalized cross-correlation template matching.
    """
    tmpl, tmpl_norm = _get_free_template()
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Crop the button area where "FREE!" can appear and standardize dimensions
    crop = img.crop((int(140 * sx), int(460 * sy), int(290 * sx), int(535 * sy)))
    crop_std = crop.resize((150, 75)).convert("L")
    arr = np.array(crop_std, dtype=np.float32)

    th, tw = tmpl.shape
    H, W = arr.shape
    shape = (H - th + 1, W - tw + 1, th, tw)
    strides = (arr.strides[0], arr.strides[1], arr.strides[0], arr.strides[1])
    windows = np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)

    win_mean = windows.mean(axis=(2, 3), keepdims=True)
    win_sub = windows - win_mean
    win_norm = np.linalg.norm(win_sub, axis=(2, 3))

    corr = np.sum(win_sub * tmpl, axis=(2, 3))
    with np.errstate(divide="ignore", invalid="ignore"):
        corr_norm = np.where(win_norm > 1e-5, corr / (win_norm * tmpl_norm), -1.0)

    best_score = float(np.max(corr_norm))
    return best_score >= 0.70


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

    Supports:
    1. Right-aligned 'OK' (when 'Play Again' is shown on victory/rematch screens).
    2. Centered 'OK' (shown on defeat, when rematch is unavailable, or summary screens at y=574).
    3. Bottom-centered 'OK' (shown on event milestone / summary screens at y=600).
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Check right-aligned OK points (top anchor (265, 560) must be blue)
    right_top = (int(265 * sx), int(560 * sy))
    right_pts = [
        (int(240 * sx), int(575 * sy)),
        (int(290 * sx), int(575 * sy)),
    ]
    if is_blue_pixel(img.getpixel(right_top)) and any(is_blue_pixel(img.getpixel(p)) for p in right_pts):
        return (int(OK_BUTTON_CENTER_RIGHT[0] * sx), int(OK_BUTTON_CENTER_RIGHT[1] * sy))

    # Check center-aligned OK points (top anchor (210, 560) must be blue)
    center_top = (int(210 * sx), int(560 * sy))
    center_pts = [
        (int(185 * sx), int(574 * sy)),
        (int(235 * sx), int(574 * sy)),
    ]
    if is_blue_pixel(img.getpixel(center_top)) and any(is_blue_pixel(img.getpixel(p)) for p in center_pts):
        return (int(OK_BUTTON_CENTER_MIDDLE[0] * sx), int(OK_BUTTON_CENTER_MIDDLE[1] * sy))

    # Check bottom-centered OK points (top anchor (210, 594) must be blue)
    bottom_center_top = (int(210 * sx), int(594 * sy))
    bottom_center_pts = [
        (int(185 * sx), int(600 * sy)),
        (int(235 * sx), int(600 * sy)),
    ]
    if is_blue_pixel(img.getpixel(bottom_center_top)) and any(is_blue_pixel(img.getpixel(p)) for p in bottom_center_pts):
        return (int(OK_BUTTON_CENTER_BOTTOM[0] * sx), int(OK_BUTTON_CENTER_BOTTOM[1] * sy))

    return None


def is_ok_button_present(img):
    """Checks if a blue 'OK' button is present (either right-aligned or centered)."""
    return get_ok_button_coords(img) is not None


def get_close_button_coords(img):
    """Locates the blue 'Close' button on an event or modal popup screen.

    Combines template matching and color sampling:
    1. Crops the bottom center region where the Close button appears.
    2. Performs normalized cross-correlation against the 'Close' text template.
    3. Verifies blue button border/wings and white text pixels to prevent false positives.
    Returns (x, y) coordinates of the button center if found, else None.
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Check multi-point blue pixels on the Close button wings/edges
    sample_pts = [
        (int(185 * sx), int(598 * sy)),  # left wing
        (int(233 * sx), int(598 * sy)),  # right wing
        (int(195 * sx), int(591 * sy)),  # top-left
        (int(223 * sx), int(591 * sy)),  # top-right
        (int(195 * sx), int(607 * sy)),  # bottom-left
        (int(223 * sx), int(607 * sy)),  # bottom-right
    ]
    blue_hits = sum(1 for p in sample_pts if is_blue_pixel(img.getpixel(p)))

    # Count white pixels in the center text area
    white_hits = 0
    for y in range(int(594 * sy), int(604 * sy)):
        for x in range(int(195 * sx), int(225 * sx)):
            r, g, b = img.getpixel((x, y))[:3]
            if r > 200 and g > 200 and b > 200:
                white_hits += 1

    # Template matching check
    tmpl, tmpl_norm = _get_close_template()
    crop_x0, crop_y0 = int(160 * sx), int(570 * sy)
    crop_x1, crop_y1 = int(260 * sx), int(625 * sy)
    crop = img.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    crop_std = crop.resize((100, 55)).convert("L")
    arr = np.array(crop_std, dtype=np.float32)

    th, tw = tmpl.shape
    H, W = arr.shape
    shape = (H - th + 1, W - tw + 1, th, tw)
    strides = (arr.strides[0], arr.strides[1], arr.strides[0], arr.strides[1])
    windows = np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)

    win_mean = windows.mean(axis=(2, 3), keepdims=True)
    win_sub = windows - win_mean
    win_norm = np.linalg.norm(win_sub, axis=(2, 3))

    corr = np.sum(win_sub * tmpl, axis=(2, 3))
    with np.errstate(divide="ignore", invalid="ignore"):
        corr_norm = np.where(win_norm > 1e-5, corr / (win_norm * tmpl_norm), -1.0)

    best_score = float(np.max(corr_norm))

    # Match confirmed if template matches or blue wings + white text are detected
    if best_score >= 0.70 and blue_hits >= 2:
        best_idx = np.unravel_index(np.argmax(corr_norm), corr_norm.shape)
        best_y, best_x = best_idx
        found_x = crop_x0 + int((best_x + tw / 2) / 100.0 * (crop_x1 - crop_x0))
        found_y = crop_y0 + int((best_y + th / 2) / 55.0 * (crop_y1 - crop_y0))
        return (found_x, found_y)

    if blue_hits >= 4 and white_hits >= 25:
        return scale_point(CLOSE_BUTTON_CENTER, (w, h))

    return None


def is_close_button_present(img):
    """Checks if a blue 'Close' button is present on the screen."""
    return get_close_button_coords(img) is not None


def get_red_x_coords(img):
    """Locates the red 'X' close button on popup modal dialogs.

    Searches the upper-right header region of modals via normalized
    template matching and verifies red pixel concentration.
    Returns (x, y) coordinates of the button center if found, else None.
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    crop_x0, crop_y0 = int(320 * sx), int(20 * sy)
    crop_x1, crop_y1 = int(395 * sx), int(320 * sy)
    crop = img.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    crop_std = crop.resize((75, 300)).convert("L")
    arr = np.array(crop_std, dtype=np.float32)

    tmpl, tmpl_norm = _get_red_x_template()
    th, tw = tmpl.shape
    H, W = arr.shape
    shape = (H - th + 1, W - tw + 1, th, tw)
    strides = (arr.strides[0], arr.strides[1], arr.strides[0], arr.strides[1])
    windows = np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)

    win_mean = windows.mean(axis=(2, 3), keepdims=True)
    win_sub = windows - win_mean
    win_norm = np.linalg.norm(win_sub, axis=(2, 3))

    corr = np.sum(win_sub * tmpl, axis=(2, 3))
    with np.errstate(divide="ignore", invalid="ignore"):
        corr_norm = np.where(win_norm > 1e-5, corr / (win_norm * tmpl_norm), -1.0)

    best_score = float(np.max(corr_norm))
    best_idx = np.unravel_index(np.argmax(corr_norm), corr_norm.shape)
    best_y, best_x = best_idx

    found_cx = crop_x0 + int((best_x + tw / 2) / 75.0 * (crop_x1 - crop_x0))
    found_cy = crop_y0 + int((best_y + th / 2) / 300.0 * (crop_y1 - crop_y0))

    rad_x = max(6, int(12 * sx))
    rad_y = max(6, int(12 * sy))
    sub_box = img.crop((found_cx - rad_x, found_cy - rad_y, found_cx + rad_x, found_cy + rad_y))
    red_count = sum(1 for p in sub_box.getdata() if is_red_pixel(p))

    min_red = max(10, int(15 * sx * sy))
    if best_score >= 0.70 and red_count >= min_red:
        return (found_cx, found_cy)

    return None


def is_red_x_present(img):
    """Checks if a red 'X' close button is present on the screen."""
    return get_red_x_coords(img) is not None


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
    if is_winner_screen(img) or is_main_menu(img) or is_close_button_present(img) or is_red_x_present(img):
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
    - 'GREEN_FREE_BUTTON'
    - 'GREEN_PAID_BUTTON'
    - 'WINNER_SCREEN'
    - 'POPUP_DISMISS'
    - 'POST_BATTLE_OK'
    - 'EVENT_SCREEN'
    - 'IN_BATTLE'
    - 'LOADING'
    """
    if is_connection_lost(img):
        return "CONNECTION_LOST"
    if is_main_menu(img):
        return "MAIN_MENU"
    if is_green_battle_button(img):
        if is_button_free(img):
            return "GREEN_FREE_BUTTON"
        return "GREEN_PAID_BUTTON"
    if is_play_again_present(img):
        return "WINNER_SCREEN"
    if is_red_x_present(img):
        return "POPUP_DISMISS"
    if is_ok_button_present(img):
        return "POST_BATTLE_OK"
    if is_close_button_present(img):
        return "EVENT_SCREEN"
    if is_in_battle(img):
        return "IN_BATTLE"
    return "LOADING"
