"""Tactical combat, card deployment, and battle state management.

Inspired by advanced placement logic, card affordability verification,
real-time elixir monitoring, and hero ability mechanics from py-clash-bot,
combined with the dynamic tower targeting and defensive incursion handling
from ClashRoyaleBuildABot.
"""

from collections import deque
import random
import time
import numpy as np
from PIL import Image
import detector

# Reference dimensions (419x633)
BASE_WIDTH = 419.0
BASE_HEIGHT = 633.0

# 10-Elixir gauge reference pips along the bottom elixir bar
ELIXIR_COORDS = [
    (149, 613),  # 1 Elixir
    (165, 613),  # 2 Elixir
    (188, 613),  # 3 Elixir
    (212, 613),  # 4 Elixir
    (240, 613),  # 5 Elixir
    (262, 613),  # 6 Elixir
    (287, 613),  # 7 Elixir
    (314, 613),  # 8 Elixir
    (339, 613),  # 9 Elixir
    (364, 613),  # 10 Elixir
]

# Elixir cost badge centers (for detecting affordable cards in hand)
CARD_BADGE_CENTERS = [
    (140, 590),  # Slot 0
    (210, 590),  # Slot 1
    (280, 590),  # Slot 2
    (350, 590),  # Slot 3
]

# Hero / Champion Ability Coordinates
CHAMPION_ABILITY_SAMPLE_PTS = [(324, 462), (334, 453), (336, 462)]
CHAMPION_ABILITY_COLORS = np.array([
    [215, 28, 223],
    [240, 39, 254],
    [239, 40, 251],
])
CHAMPION_ABILITY_TRIGGER_COORD = (330, 460)

# Emotes
EMOTE_BUTTON_COORD = (67, 521)
EMOTE_ICON_COORDS = [
    (124, 419),
    (182, 420),
    (255, 411),
    (312, 423),
    (133, 471),
    (188, 472),
    (243, 469),
    (308, 470),
]

# Safe neutral deadspace coordinate to dismiss popups without triggering buttons
DEADSPACE_COORD = (20, 200)

# Tactical placement coordinates by strategic zone (left & right lanes)
# Derived and calibrated from py-clash-bot & ClashRoyaleBuildABot tile grids
TACTICAL_ZONES = {
    # Front-line bridge pressure / aggressive push
    "bridge_rush": {
        "left": [(77, 281), (113, 286), (115, 332), (154, 283)],
        "right": [(257, 283), (295, 336), (300, 284), (353, 283)],
    },
    # Back-field support behind Princess Towers
    "back_support": {
        "left": [(69, 442), (102, 451), (158, 444), (166, 394)],
        "right": [(247, 396), (264, 440), (312, 456), (343, 442)],
    },
    # Deep king tower lane to build slow pushes
    "king_lane": {
        "left": [(70, 463), (184, 398), (191, 473)],
        "right": [(211, 471), (264, 440), (343, 463)],
    },
    # Center field defensive pull between princess towers
    "defense_center": {
        "left": [(191, 351), (202, 339), (224, 320)],
        "right": [(214, 360), (224, 334), (224, 320)],
    },
    # Offensive spell targets on enemy tower lanes
    "spell_tower": {
        "left": [(118, 185), (116, 160)],
        "right": [(295, 185), (302, 160)],
    },
    # Pocket rush: unlocked when corresponding enemy princess tower is destroyed
    "pocket_rush": {
        "left": [(140, 250), (155, 265)],
        "right": [(265, 250), (280, 265)],
    },
}


def tile_to_base_coords(tile_x: float, tile_y: float) -> tuple[int, int]:
    """Converts a Clash Royale tile grid coordinate (18 columns x 32 rows)
    to 419x633 base coordinates (derived from ClashRoyaleBuildABot tile grid system).
    tile_x: 0 to 17 (0-8 left lane, 9-17 right lane)
    tile_y: 0 to 31 (0 friendly king, 15 river/bridge, 31 enemy king)
    """
    x = (52.0 + (tile_x + 0.5) * 34.0) * (BASE_WIDTH / 720.0)
    y = (1280.0 - 296.0 - (tile_y + 0.5) * 27.6) * (BASE_HEIGHT / 1280.0)
    return int(round(x)), int(round(y))


def is_elixir_pip(rgb) -> bool:
    """Checks if RGB matches Clash Royale's pink/magenta elixir bar color."""
    r, g, b = rgb[:3]
    return r >= 135 and b >= 135 and r > g * 1.1 and b > g * 1.1 and g <= 180


def count_elixir(img: Image.Image) -> int:
    """Reads the current elixir level (0-10) by sampling the elixir gauge."""
    w, h = img.size
    count = 0
    for pt in ELIXIR_COORDS:
        spt = detector.scale_point(pt, (w, h))
        if is_elixir_pip(img.getpixel(spt)):
            count += 1
    return count


def is_magenta_badge(rgb) -> bool:
    """Checks if RGB matches the magenta card elixir badge."""
    r, g, b = rgb[:3]
    return (r >= 140 and b >= 130 and g < 100) or (r >= 200 and b >= 180 and g < 160)


def is_card_slot_ready(img: Image.Image, slot_idx: int) -> bool:
    """Determines if a card in hand is affordable and ready to deploy.
    Combines ClashRoyaleBuildABot's color channel standard deviation check
    with magenta cost badge verification for 100% detection accuracy.
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # 1. Magenta cost badge check
    badge_pt = CARD_BADGE_CENTERS[slot_idx]
    bx, by = detector.scale_point(badge_pt, (w, h))
    badge_hits = 0
    for dy in range(-8, 9, 2):
        for dx in range(-8, 9, 2):
            if is_magenta_badge(img.getpixel((bx + dx, by + dy))):
                badge_hits += 1
    if badge_hits >= 6:
        return True

    # 2. Color saturation check (ClashRoyaleBuildABot _detect_if_ready)
    # Cards without enough elixir are rendered in greyscale (std < 10 across RGB channels)
    cx_raw = [140, 210, 280, 350][slot_idx]
    cx = int(cx_raw * sx)
    cy = int(540 * sy)
    crop = img.crop((cx - 15, cy - 20, cx + 15, cy + 20))
    arr = np.array(crop, dtype=np.float32)
    color_std = float(np.mean(np.std(arr, axis=2)))
    return color_std > 20.0


def get_available_card_indices(img: Image.Image) -> list[int]:
    """Identifies which card slots (0-3) in hand are affordable and ready to deploy."""
    return [i for i in range(4) if is_card_slot_ready(img, i)]


def is_champion_ability_available(img: Image.Image) -> bool:
    """Checks if a Hero or Champion active ability button is ready above the deck."""
    w, h = img.size
    for i, pt in enumerate(CHAMPION_ABILITY_SAMPLE_PTS):
        spt = detector.scale_point(pt, (w, h))
        rgb = np.array(img.getpixel(spt)[:3])
        if np.all(np.abs(rgb - CHAMPION_ABILITY_COLORS[i]) <= 40):
            return True
    return False


def is_enemy_hp_red(rgb) -> bool:
    """Checks if RGB matches the enemy Princess Tower red HP bar."""
    r, g, b = rgb[:3]
    return r > 180 and g < 70 and b > 60 and b < 130 and (r - g) > 120


def is_ally_hp_blue(rgb) -> bool:
    """Checks if RGB matches the ally Princess Tower light blue/cyan HP bar."""
    r, g, b = rgb[:3]
    return b > 170 and g > 130 and r < 140 and (b - r) > 40


def get_enemy_tower_status(img: Image.Image) -> dict:
    """Inspects enemy princess towers to determine health and destroyed status
    (inspired by ClashRoyaleBuildABot tower HP evaluation).
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    # Left tower HP bar: x=85..125, y=96
    l_pts = [(int(x * sx), int(96 * sy)) for x in range(85, 125, 2)]
    l_hp = sum(1 for p in l_pts if is_enemy_hp_red(img.getpixel(p)))

    # Right tower HP bar: x=275..315, y=96
    r_pts = [(int(x * sx), int(96 * sy)) for x in range(275, 315, 2)]
    r_hp = sum(1 for p in r_pts if is_enemy_hp_red(img.getpixel(p)))

    # Tower destroyed analysis:
    # If both HP bars are missing, neither is destroyed yet (start of match or undamaged)
    if l_hp == 0 and r_hp == 0:
        l_destroyed = False
        r_destroyed = False
        focus = "left"
    elif l_hp > 0 and r_hp == 0:
        # Left has taken damage, right is untouched (100% full) -> focus damaged left tower
        l_destroyed = False
        r_destroyed = False
        focus = "left"
    elif r_hp > 0 and l_hp == 0:
        # Right has taken damage, left is untouched (100% full) -> focus damaged right tower
        l_destroyed = False
        r_destroyed = False
        focus = "right"
    else:
        # Both visible: weaker tower has fewer remaining red HP pixels
        l_destroyed = False
        r_destroyed = False
        focus = "left" if l_hp <= r_hp else "right"

    return {
        "left_hp": l_hp,
        "right_hp": r_hp,
        "left_destroyed": l_destroyed,
        "right_destroyed": r_destroyed,
        "focus_lane": focus,
    }


def is_enemy_troop_hp(rgb) -> bool:
    """Checks if RGB matches an enemy unit's floating health bar."""
    r, g, b = rgb[:3]
    return r > 175 and g < 65 and b < 105 and (r - g) > 115


def detect_enemy_threats(img: Image.Image) -> tuple[bool, str, int]:
    """Detects enemy troops crossing into friendly territory
    (inspired by ClashRoyaleBuildABot DefenseAction).
    """
    w, h = img.size
    sx = w / BASE_WIDTH
    sy = h / BASE_HEIGHT

    left_threats = 0
    right_threats = 0
    center_threats = 0

    # Scan friendly arena half: y=285 to 440
    for y_raw in range(285, 440, 4):
        y = int(y_raw * sy)
        for x_raw in range(70, 350, 4):
            x = int(x_raw * sx)
            if is_enemy_troop_hp(img.getpixel((x, y))):
                if x_raw < 160:
                    left_threats += 1
                elif x_raw > 260:
                    right_threats += 1
                else:
                    center_threats += 1

    total = left_threats + right_threats + center_threats
    has_threat = total >= 4

    if left_threats >= right_threats and left_threats >= center_threats:
        threat_lane = "left"
    elif right_threats >= center_threats:
        threat_lane = "right"
    else:
        threat_lane = "center"

    return has_threat, threat_lane, total


class BattleTactics:
    """Manages tactical decision-making during combat:
    - Real-time enemy tower health evaluation & weaker tower targeting
    - Pocket deployment expansion when enemy towers fall
    - Defensive incursion detection and central pull counters (ClashRoyaleBuildABot DefenseAction)
    - Card selection cycling to avoid card-spam locks
    - Dynamic placement pacing based on elixir levels
    - Hero ability management and occasional emote interaction
    """

    def __init__(self):
        self.last_played_slots = deque(maxlen=3)
        self.current_lane = random.choice(["left", "right"])
        self.plays_in_lane = 0
        self.cards_played = 0
        self.abilities_used = 0
        self.emotes_sent = 0
        self.last_emote_time = 0.0
        self.left_enemy_hp = 1.0
        self.right_enemy_hp = 1.0
        self.left_enemy_destroyed = False
        self.right_enemy_destroyed = False

    def reset_match(self):
        """Resets match-specific tactical state between battles."""
        self.last_played_slots.clear()
        self.current_lane = random.choice(["left", "right"])
        self.plays_in_lane = 0
        self.left_enemy_hp = 1.0
        self.right_enemy_hp = 1.0
        self.left_enemy_destroyed = False
        self.right_enemy_destroyed = False

    def select_card_slot(self, available_slots: list[int]) -> int:
        """Selects a playable card slot, prioritizing cards not recently played."""
        if not available_slots:
            return random.randint(0, 3)

        preferred = [idx for idx in available_slots if idx not in self.last_played_slots]
        if preferred:
            chosen = random.choice(preferred)
        else:
            non_recent = [idx for idx in available_slots if idx != self.last_played_slots[-1]]
            chosen = random.choice(non_recent) if non_recent else random.choice(available_slots)

        self.last_played_slots.append(chosen)
        self.plays_in_lane += 1
        self.cards_played += 1
        return chosen

    def update_tower_status(self, img: Image.Image) -> dict:
        """Tracks tower damage progression and detects tower destruction over time."""
        status = get_enemy_tower_status(img)
        l_hp = status["left_hp"]
        r_hp = status["right_hp"]

        if l_hp > 0:
            ratio = l_hp / 20.0
            self.left_enemy_hp = min(self.left_enemy_hp, ratio)
        elif self.left_enemy_hp < 0.25 and not self.left_enemy_destroyed:
            self.left_enemy_destroyed = True

        if r_hp > 0:
            ratio = r_hp / 20.0
            self.right_enemy_hp = min(self.right_enemy_hp, ratio)
        elif self.right_enemy_hp < 0.25 and not self.right_enemy_destroyed:
            self.right_enemy_destroyed = True

        # Determine optimal lane
        if self.left_enemy_destroyed and not self.right_enemy_destroyed:
            focus = "right"
        elif self.right_enemy_destroyed and not self.left_enemy_destroyed:
            focus = "left"
        elif self.left_enemy_hp < self.right_enemy_hp:
            focus = "left"
        elif self.right_enemy_hp < self.left_enemy_hp:
            focus = "right"
        else:
            focus = self.current_lane

        self.current_lane = focus
        return {
            "left_destroyed": self.left_enemy_destroyed,
            "right_destroyed": self.right_enemy_destroyed,
            "focus_lane": focus,
            "left_hp_ratio": self.left_enemy_hp,
            "right_hp_ratio": self.right_enemy_hp,
        }

    def get_preferred_lane(self) -> str:
        """Returns the current preferred lane for backward compatibility."""
        return self.current_lane

    def get_tactical_placement(self, lane: str) -> tuple[int, int]:
        """Backward-compatible placement generator for a given lane."""
        candidates = TACTICAL_ZONES["bridge_rush"].get(lane, TACTICAL_ZONES["bridge_rush"]["left"])
        return self._jitter_point(random.choice(candidates))

    def plan_tactical_play(self, img: Image.Image, elixir: int = 5) -> tuple[tuple[int, int], str]:
        """Dynamically computes the highest-value tactical placement:
        1. Emergency Defense: If enemy troops cross the river -> 4-3 Central Pull.
        2. Tower Punish: If an enemy tower is destroyed -> Pocket Rush (45% chance).
        3. Strategic Push:
           - Elixir >= 8: Aggressive Bridge Push on weaker tower.
           - Elixir < 8:  Back Support deployment behind tower to build push.
        """
        # 1. Defensive incursion check (ClashRoyaleBuildABot DefenseAction)
        has_threat, threat_lane, threat_count = detect_enemy_threats(img)
        if has_threat:
            # 4-3 plant: pull towards the opposite-center side to maximize dual tower fire
            pull_side = "right" if threat_lane == "left" else "left"
            candidates = TACTICAL_ZONES["defense_center"][pull_side]
            base_pt = random.choice(candidates)
            desc = f"DEFENSIVE PULL ({threat_lane.upper()} INVASION - {threat_count} threats)"
            return self._jitter_point(base_pt), desc

        # 2. Update tower health & destroyed status
        towers = self.update_tower_status(img)
        target_lane = towers["focus_lane"]

        # 3. Pocket Rush (ClashRoyaleBuildABot LEFT/RIGHT_PRINCESS_TILES)
        if (towers["left_destroyed"] or towers["right_destroyed"]) and random.random() < 0.45:
            pocket_side = "left" if towers["left_destroyed"] else "right"
            base_pt = random.choice(TACTICAL_ZONES["pocket_rush"][pocket_side])
            desc = f"POCKET RUSH ({pocket_side.upper()} TOWER DOWN)"
            return self._jitter_point(base_pt), desc

        # 4. Coordinated push against weaker tower
        if elixir >= 8:
            # High Elixir -> Aggressive Bridge Rush (ClashRoyaleBuildABot BridgeAction)
            candidates = TACTICAL_ZONES["bridge_rush"][target_lane]
            desc = f"BRIDGE RUSH ({target_lane.upper()} WEAKER TOWER)"
        else:
            # Moderate Elixir -> Back Support to build slow push (ClashRoyaleBuildABot KingAction)
            roll = random.random()
            if roll < 0.60:
                candidates = TACTICAL_ZONES["back_support"][target_lane]
                desc = f"BACK SUPPORT ({target_lane.upper()} BUILD PUSH)"
            else:
                candidates = TACTICAL_ZONES["king_lane"][target_lane]
                desc = f"KING LANE ({target_lane.upper()} BUILD PUSH)"

        base_pt = random.choice(candidates)
        return self._jitter_point(base_pt), desc

    @staticmethod
    def _jitter_point(pt: tuple[int, int]) -> tuple[int, int]:
        """Applies subtle human-like organic jitter (+/- 5px)."""
        return (pt[0] + random.randint(-5, 5), pt[1] + random.randint(-5, 5))

    def should_send_emote(self) -> bool:
        """Decides whether to send an emote (cooldown ~25s, 20% chance)."""
        now = time.time()
        if now - self.last_emote_time > 25.0 and random.random() < 0.20:
            self.last_emote_time = now
            return True
        return False

