import pygame
print("CUBE JUMPER loading!")
import sys
import random
import os
import json
def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

SETTINGS_FILE = "settings.json"
HIGHSCORE_FILE = "highscore.txt"
DEATH_SCORE_THRESHOLD = 55
armed = False
ARM_SCORE = 55
KILL_SCORE = 1
FALL_DEATH_ENABLED = True
DEBUG_LAND_PRINTS = False

# =========================
# Color unlocks
# =========================
COLOR_UNLOCKS = [
    ("Red",(255, 0, 0),0),
    ("Light Blue",(75, 157, 250),150),
    ("Dark Blue",(5, 0, 255),150),
    ("Light Green",(0, 200, 80),300),
    ("Dark Green",(0, 92, 16),300),
    ("White",(255, 255, 255),500),
    ("Grey",(138, 138, 138),625),
    ("Yellow",(255, 200, 0),750),
    ("Orange",(255, 98, 0),1000),
    ("Purple",(170, 60, 255),1500),
    ("Pink",(255, 0, 122),1750),
    ("Black",(0, 0, 0,),2000),
]

COLOR_BY_NAME = {name: rgb for (name, rgb, _) in COLOR_UNLOCKS}
UNLOCK_SCORE_BY_NAME = {name: unlock for (name, _, unlock) in COLOR_UNLOCKS}
COLOR_NAMES = [name for (name, _, _) in COLOR_UNLOCKS]

# =========================
# Settings helpers
# =========================
show_controls = True
show_live_score = False
show_lvl = True
selected_color_name = "Red"
unlocked_colors = {"Red"}

def load_settings():
    global show_controls, show_live_score, selected_color_name, unlocked_colors, show_lvl
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            show_controls = bool(data.get("show_controls", True))
            show_live_score = bool(data.get("show_live_score", True))
            show_lvl = bool(data.get("show_lvl", True))
            selected_color_name = str(data.get("selected_color", "Red"))
            if selected_color_name not in COLOR_BY_NAME:
                selected_color_name = "Red"
            saved_unlocked = data.get("unlocked_colors", ["Red"])
            if isinstance(saved_unlocked, list):
                unlocked_colors = set([c for c in saved_unlocked if c in COLOR_BY_NAME])
            else:
                unlocked_colors = {"Red"}
            if "Red" not in unlocked_colors:
                unlocked_colors.add("Red")
            if selected_color_name not in unlocked_colors:
                selected_color_name = "Red"
        except:
            pass

def save_settings():
    try:
        data = {
            "show_lvl": show_lvl,
            "show_controls": show_controls,
            "show_live_score": show_live_score,
            "selected_color": selected_color_name,
            "unlocked_colors": sorted(list(unlocked_colors), key=lambda n: COLOR_NAMES.index(n)),
            }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def update_color_unlocks(current_score: int):
    global unlocked_colors, selected_color_name
    changed = False
    for name, _, unlock_score in COLOR_UNLOCKS:
        if current_score >= unlock_score and name not in unlocked_colors:
            unlocked_colors.add(name)
            changed = True
    if changed:
        if selected_color_name not in unlocked_colors:
            selected_color_name = "Red"
        save_settings()

def set_selected_color(name: str):
    global selected_color_name
    if name in unlocked_colors:
        selected_color_name = name
        save_settings()

# =========================
# High score helpers
# =========================
def load_high_score():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(value):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(value))
    except:
        pass

# =========================
# Init
# =========================
pygame.init()
load_settings()

# Window
WIDTH, HEIGHT = 1800, 900
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
screen = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("CUBE JUMPER!")
fullscreen = False

icon = pygame.image.load(resource_path("cube_jumper.png")).convert_alpha()
pygame.display.set_icon(icon)

clock = pygame.time.Clock()

# =========================
# Survival stats
# =========================
MAX_STAT = 100

health = 100
food = 100
water = 100

FOOD_DPS = 0.6
WATER_DPS = 0.9

STARVE_HDPS = 2.5
DEHYDRATE_HDPS = 3.0

last_stat_tick = pygame.time.get_ticks()

# Text
small_font = pygame.font.SysFont(None, 22)
font = pygame.font.SysFont(None, 32)
big_font = pygame.font.SysFont(None, 64)
score_font = pygame.font.SysFont(None, 64)

# =========================
# Load house PNG assets
# =========================
ASSET_DIR = resource_path("assets")
HOUSE_DIR = resource_path("assets", "houses")

HOUSE_IMAGES = []
if os.path.isdir(HOUSE_DIR):
    for fname in os.listdir(HOUSE_DIR):
        if fname.lower().endswith(".png"):
            path = os.path.join(HOUSE_DIR, fname)
            try:
                img = pygame.image.load(path).convert_alpha()
                HOUSE_IMAGES.append(img)
            except Exception as e:
                print(f"WARNING: Failed to load {path}: {e}")

if not HOUSE_IMAGES:
    print("WARNING: No house PNGs found in assets/houses/")

# =========================
# Item icons
# =========================
ITEM_DIR = resource_path("assets", "items")

def load_icon(filename):
    path = os.path.join(ITEM_DIR, filename)
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"WARNING: Failed to load {path}: {e}")
        return None
    
PLANK_ICON = load_icon("plank.png")
METAL_PIPE_ICON = load_icon("metal_pipe.png")
ROCK_ICON = load_icon("rock.png")
STICK_ICON = load_icon("stick.png")
WATER_BOTTLE_ICON = load_icon("water_bottle.png")
MEAT_ICON = load_icon("meat.png")
APPLE_ICON = load_icon("apple.png")

# =========================
# Inventory
# =========================
world_items = []
inventory_open = False
INVENTORY_SLOTS = 9
inventory = [None] * INVENTORY_SLOTS
selected_slot = 0
inv_slots_rects = []
context_open = False
VILLAGE_LOOT_POOL = ["Apple", "Water Bottle", "Meat"]
context_slot = None
context_item_name = None
context_action = None
context_rect = pygame.Rect(0, 0, 220, 120)
context_use_btn = pygame.Rect(0, 0, 180, 50)
context_close_btn = pygame.Rect(0, 0, 180, 40)
ITEM_ICONS = {
"Plank": PLANK_ICON,
"Apple": APPLE_ICON,
"Meat": MEAT_ICON,
"Water Bottle": WATER_BOTTLE_ICON,
}
def draw_inventory(screen, font, selected_slot, inventory):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 420, 470
    panel = pygame.Rect(WIDTH // 2 - panel_w // 2, HEIGHT // 2 - panel_h // 2, panel_w, panel_h)
    pygame.draw.rect(screen, (40, 40, 40), panel, border_radius=14)
    pygame.draw.rect(screen, (255, 255, 255), panel, 2, border_radius=14)

    title = big_font.render("INVENTORY", True, (255, 255, 255))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 20))

    slots = []
    slot_size = 100
    gap = 12
    grid_w = 3 * slot_size + 2 * gap
    grid_h = 3 * slot_size + 2 * gap
    grid_x = panel.centerx - grid_w // 2
    grid_y = panel.y + 110

    idx = 0
    for r in range(3):
        for c in range(3):
            rect = pygame.Rect(
                grid_x + c * (slot_size + gap),
                grid_y + r * (slot_size + gap),
                slot_size,
                slot_size,
            )
            slots.append(rect)

            pygame.draw.rect(screen, (70, 70, 70), rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=10)

            if selected_slot is not None and idx == selected_slot:
                pygame.draw.rect(screen, (255, 220, 120), rect, 4, border_radius=10)

            item = inventory[idx]
            if item is not None:
                name = item.get("name") if isinstance(item, dict) else str(item)

                icon = None
                if name == "Plank":
                    icon = PLANK_ICON
                elif name == "Metal Pipe":
                    icon = METAL_PIPE_ICON
                elif name == "Rock":
                    icon = ROCK_ICON
                elif name == "Stick":
                    icon = STICK_ICON
                elif name == "Water Bottle":
                    icon = WATER_BOTTLE_ICON
                elif name == "Meat":
                    icon = MEAT_ICON
                elif name == "Apple":
                    icon = APPLE_ICON

                if icon:
                    pad = 14
                    target = slot_size - pad * 2

                    iw, ih = icon.get_size()
                    scale = min(target / iw, target / ih)
                    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                    icon_s = pygame.transform.smoothscale(icon, (nw, nh))

                    icon_y = rect.y + 10
                    screen.blit(icon_s, (rect.centerx - nw // 2, icon_y))

                    label = name
                    label_surf = small_font.render(label, True, (235, 235, 235))
                    label_x = rect.centerx - label_surf.get_width() //2
                    label_y = rect.bottom - label_surf.get_height() - 8
                    screen.blit(label_surf, (label_x, label_y))
                    
                    count = int(item.get("count", 1))
                    if count > 1:
                        count_surf = small_font.render(str(count), True, (255, 255, 255))
                        screen.blit(count_surf, (rect.right - count_surf.get_width() - 8, rect.bottom - count_surf.get_height() - 8))

                else:
                    txt = font.render(name, True, (255, 255, 255))
                    screen.blit(txt, (rect.x + 8, rect.y + 8))

            idx += 1

    hint = font.render("Click a slot • E to close", True, (220, 220, 220))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 60))

    return slots

ITEM_DEFS = {
    "Plank": {"stackable": False},
    "Metal Pipe": {"stackable": False},
    "Water Bottle": {"stackable": False},
    "Meat": {"stackable": False},

    # stackables
    "Stick": {"stackable": True, "max_stack": 8},
    "Rock": {"stackable": True, "max_stack": 8},
    "Apple": {"stackable": True, "max_stack": 8},
}

def add_item_to_inventory(item_name: str, amount: int = 1) -> bool:
    if item_name not in ITEM_DEFS or amount <= 0:
        return False
    
    stackable = ITEM_DEFS[item_name].get("stackable", True)
    max_stack = int(ITEM_DEFS[item_name].get("max_stack", 8))

    if not stackable:
        for _ in range(amount):
            placed = False
            for i in range(len(inventory)):
                if inventory[i] is None:
                    inventory[i] = {"name": item_name, "count": 1}
                    placed = True
                    break
            if not placed:
                return False
        return True

    remaining = amount

    for i in range(len(inventory)):
        it = inventory[i]
        if isinstance(it, dict) and it.get("name") == item_name:
            current = int(it.get("count", 1))
            if current < max_stack:
                space = max_stack - current
                add_now = min(space, remaining)
                it["count"] = current + add_now
                remaining -= add_now
                if remaining <= 0:
                    return True

    # Put remaining into new stacks
    for i in range(len(inventory)):
        if inventory[i] is None:
            add_now = min(max_stack, remaining)
            inventory[i] = {"name": item_name, "count": add_now}
            remaining -= add_now
            if remaining <= 0:
                return True

    # No space for the rest
    return False

# Camera
camera_y = 0

# Pause
paused = False
btn_w, btn_h = 260, 60
btn_x = WIDTH // 2 - btn_w // 2
resume_btn = pygame.Rect(btn_x, 260, btn_w, btn_h)
restart_btn = pygame.Rect(btn_x, 340, btn_w, btn_h)
settings_btn = pygame.Rect(btn_x, 420, btn_w, btn_h)
customize_btn = pygame.Rect(btn_x, 500, btn_w, btn_h)
quit_btn = pygame.Rect(btn_x, 580, btn_w, btn_h)
toggle_controls_btn = pygame.Rect(btn_x, 300, btn_w, btn_h)
back_btn = pygame.Rect(btn_x, 540, btn_w, btn_h)
toggle_lvl_btn = pygame.Rect(btn_x, 460, btn_w, btn_h)
in_settings = False
in_customize = False
toggle_live_score_btn = pygame.Rect(btn_x, 380, btn_w, btn_h)
cust_prev_btn = pygame.Rect(btn_x - 160, 360, 140, 60)
cust_next_btn = pygame.Rect(btn_x + btn_w + 20, 360, 140, 60)
cust_select_btn = pygame.Rect(btn_x, 440, btn_w, btn_h)
cust_back_btn = pygame.Rect(btn_x, 520, btn_w, btn_h)
cust_index = COLOR_NAMES.index(selected_color_name) if selected_color_name in COLOR_NAMES else 0

# Game over
game_over = False
new_high = False
dead = True  # True => shows "YOU DIED" (ground death). False => shows "GAME OVER"
fell = False # True => shows "YOU FELL" (ground death). False => shows "GAME OVER"

# PLAYER
player = pygame.Rect(50, 300, 40, 40)
player_vel_y = 0
speed = 5
jump_power = -12
gravity = 0.6
on_ground = False
move_dir = 1

# Score
score = 0
best_y = player.y
live_score = 0

# High score
high_score = load_high_score()

# Dash
dash_speed = 150
dash_cooldown = 2500
last_dash_time = -dash_cooldown

# Ground
ground = pygame.Rect(0, 350, WIDTH, HEIGHT // 2)

FALL_DEATH_HEIGHT = 420
fall_peak_y = None

# =========================
# Platform generation
# =========================
platforms = []
highest_plat_y = 0
last_plat_x = WIDTH // 2

MAX_PLAT_DX_BASE = 320
EDGE_MARGIN = 20
PLAT_MIN_W_BASE = 170
PLAT_MAX_W_BASE = 220
PLAT_H = 20
GAP_MIN_Y_BASE = 80
GAP_MAX_Y_BASE = 100

# =========================
# Town platforms + Houses
# =========================
TOWN_SCORE_STEP = 500   
TOWN_SPAWN_OFFSET = 5       # every ~500 score
TOWN_PLAT_W = WIDTH            # big platform across the whole screen
TOWN_PLAT_H = 30
HOUSES_PER_TOWN = (4, 10)       # random range

town_platforms = []            # list[pygame.Rect]
houses = []                    # list[dict]: {"x","y","surf","w","h"}
next_town_score = TOWN_SCORE_STEP

def make_house_surface(style: int = 0) -> pygame.Surface:
    w, h = 120, 110
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # body
    pygame.draw.rect(surf, (200, 170, 120), pygame.Rect(15, 45, 90, 55), border_radius=6)

    # roof
    pygame.draw.polygon(surf, (160, 60, 60), [(10, 50), (60, 15), (110, 50)])

    # door
    pygame.draw.rect(surf, (110, 70, 30), pygame.Rect(52, 65, 16, 35), border_radius=3)

    # windows
    pygame.draw.rect(surf, (180, 220, 255), pygame.Rect(25, 60, 16, 16), border_radius=3)
    pygame.draw.rect(surf, (180, 220, 255), pygame.Rect(79, 60, 16, 16), border_radius=3)

    # outline (optional)
    pygame.draw.rect(surf, (20, 20, 20), pygame.Rect(15, 45, 90, 55), 2, border_radius=6)
    pygame.draw.polygon(surf, (20, 20, 20), [(10, 50), (60, 15), (110, 50)], 2)

    return surf


def spawn_town_at_score(s: int):
    global town_platforms, houses, world_items

    town_top_y = ground.top - (s * 10)  # world Y where this town platform sits
    plat = pygame.Rect(0, town_top_y, TOWN_PLAT_W, TOWN_PLAT_H)
    town_platforms.append(plat)

    weights = {
        4: 28,
        5: 26,
        6: 21,
        7: 12,
        8: 6,
        9: 4,
        10: 3,
    }
    n = random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


    # simple spacing so houses don't overlap
    margin = 40
    usable_w = TOWN_PLAT_W - 2 * margin
    if n > 0:
        step = usable_w // n
    else:
        step = usable_w

    for i in range(n):
        if HOUSE_IMAGES:
            house_surf = random.choice(HOUSE_IMAGES)
        else:
            house_surf = make_house_surface(style=random.randint(0, 2))
        hw, hh = house_surf.get_size()

        # spread them across the platform with some randomness
        base_x = margin + i * step + step // 2 - hw // 2
        jitter = random.randint(-30, 30)
        x = max(margin, min(TOWN_PLAT_W - margin - hw, base_x + jitter))

        y = plat.top - hh  # sit on top of platform

        houses.append({"x": x, "y": y, "surf": house_surf, "w": hw, "h": hh})

    num_items = random.randint(1, 2)
    for _ in range(num_items):
        item_name = random.choice(VILLAGE_LOOT_POOL)
        item_icon = ITEM_ICONS.get(item_name)
        item_w, item_h = (32, 32)
        if item_icon:
            item_icon = pygame.transform.smoothscale(item_icon, (32, 32))
        spawn_x = random.randint(60, WIDTH - 60 - item_w)
        spawn_y = plat.top - item_h
        world_items.append({
            "name": item_name,
            "rect": pygame.Rect(spawn_x, spawn_y, item_w, item_h),
            "icon": item_icon
        })

MAX_PLAT_DX = MAX_PLAT_DX_BASE
PLAT_MIN_W = PLAT_MIN_W_BASE
PLAT_MAX_W = PLAT_MAX_W_BASE
GAP_MIN_Y = GAP_MIN_Y_BASE
GAP_MAX_Y = GAP_MAX_Y_BASE

LEVEL_SCORE_STEP = 1000
MAX_LEVEL = 12

def get_level_from_score(s: int) -> int:
    return max(1, min(MAX_LEVEL, (s // LEVEL_SCORE_STEP) + 1))

def apply_difficulty_for_score(s: int):
    global MAX_PLAT_DX, PLAT_MIN_W, PLAT_MAX_W, GAP_MIN_Y, GAP_MAX_Y
    level = get_level_from_score(s)
    t = (level - 1) / (MAX_LEVEL - 1)

    PLAT_MIN_W = int(PLAT_MIN_W_BASE - 80 * t)
    PLAT_MAX_W = int(PLAT_MAX_W_BASE - 80 * t)

    GAP_MIN_Y = int(GAP_MIN_Y_BASE + 50 * t)
    GAP_MAX_Y = int(GAP_MAX_Y_BASE + 70 * t)

    MAX_PLAT_DX = int(MAX_PLAT_DX_BASE + 100 * t)

    PLAT_MIN_W = max(60, PLAT_MIN_W)
    PLAT_MAX_W = max(PLAT_MIN_W + 20, PLAT_MAX_W)
    GAP_MIN_Y = max(60, GAP_MIN_Y)
    GAP_MAX_Y = max(GAP_MIN_Y + 5, GAP_MAX_Y)

    return level

GEN_BUFFER = 900
DESPAWN_BUFFER = 900

def build_start_platforms():
    global platforms, highest_plat_y, last_plat_x
    apply_difficulty_for_score(score)
    platforms = []
    start_y = 300

    w = random.randint(PLAT_MIN_W, PLAT_MAX_W)
    x = 200
    platforms.append(pygame.Rect(x, start_y, w, PLAT_H))
    last_plat_x = x

    y = start_y
    for _ in range(7):
        w = random.randint(PLAT_MIN_W, PLAT_MAX_W)
        gap = random.randint(GAP_MIN_Y, GAP_MAX_Y)
        y -= gap

        min_x = max(EDGE_MARGIN, last_plat_x - MAX_PLAT_DX)
        max_x = min(WIDTH - EDGE_MARGIN - w, last_plat_x + MAX_PLAT_DX)
        if min_x > max_x:
            min_x = EDGE_MARGIN
            max_x = WIDTH - EDGE_MARGIN - w

        x = random.randint(min_x, max_x)
        platforms.append(pygame.Rect(x, y, w, PLAT_H))
        last_plat_x = x

    highest_plat_y = min(p.y for p in platforms)

build_start_platforms()

# =========================
# UI helpers
# =========================
def draw_button(screen, rect, text, mouse_pos, font, disabled=False):
    hovered = rect.collidepoint(mouse_pos) and not disabled
    bg = (70, 70, 70) if not hovered else (110, 110, 110)
    border = (255, 255, 255)

    pygame.draw.rect(screen, bg, rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, 2, border_radius=10)

    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
    return hovered

def draw_stat_bar(screen, right_x, top_y, width, height, value, max_value, label, fill_color):
    bg_rect = pygame.Rect(right_x - width, top_y, width, height)
    pygame.draw.rect(screen, (0, 0, 0), bg_rect, border_radius=6)
    pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2, border_radius=6)
    pct = 0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
    fill_w = int((width - 4) * pct)
    fill_rect = pygame.Rect(bg_rect.x + 2, bg_rect.y + 2, fill_w, height - 4)
    pygame.draw.rect(screen, fill_color, fill_rect, border_radius=6)

    text = font.render(f"{label}: {int(value)}", True, (255, 255, 255))
    screen.blit(text, (bg_rect.x + 8, bg_rect.y + (height // 2 - text.get_height() // 2)))

def reset_survival_timer():
    global last_stat_tick
    last_stat_tick = pygame.time.get_ticks()

def restart_game():
    global player, player_vel_y, on_ground, move_dir, camera_y, last_dash_time, armed, in_customize, food, last_stat_tick, houses, fall_peak_y
    global paused, score, best_y, in_settings, game_over, new_high, dead, high_score, live_score, health, water, town_platforms, next_town_score, world_items

    player.x, player.y = 50, 300
    player_vel_y = 0
    on_ground = False
    move_dir = 1
    camera_y = 0
    last_dash_time = -dash_cooldown
    paused = False
    score = 0
    best_y = player.y
    in_settings = False
    in_customize = False
    game_over = False
    new_high = False
    dead = False
    armed = False
    live_score = 0
    health = 100
    food = 100
    water = 100
    last_stat_tick = pygame.time.get_ticks()
    town_platforms = []
    houses = []
    next_town_score = TOWN_SCORE_STEP
    fall_peak_y = None
    world_items = []
    build_start_platforms()

# =========================
# Physics
# =========================
def move_and_collide(rect, dx, dy, solids):
    # move X
    rect.x += dx
    for s in solids:
        if rect.colliderect(s):
            if dx > 0:
                rect.right = s.left
            elif dx < 0:
                rect.left = s.right

    # move Y
    rect.y += dy
    for s in solids:
        if rect.colliderect(s):
            if dy > 0:
                rect.bottom = s.top
            elif dy < 0:
                rect.top = s.bottom
            dy = 0

    landed_on = None
    probe = rect.move(0, 1)
    for s in solids:
        if probe.colliderect(s):
            landed_on = s
            break

    on_ground_now = (landed_on is not None)
    return dy, on_ground_now, landed_on

# =========================
# Game loop
# =========================
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Pause menu clicks
        if paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            current_w, current_h = window.get_size()
            mx = int(event.pos[0] * (WIDTH / current_w))
            my = int(event.pos[1] * (HEIGHT / current_h))
            if in_settings:
                if toggle_controls_btn.collidepoint(mx, my):
                    show_controls = not show_controls
                    save_settings()
                elif toggle_live_score_btn.collidepoint(mx, my):
                    show_live_score = not show_live_score
                    save_settings()
                elif toggle_lvl_btn.collidepoint(mx, my):
                    show_lvl = not show_lvl
                    save_settings()
                elif back_btn.collidepoint(mx, my):
                    in_settings = False
            elif in_customize:
                if cust_prev_btn.collidepoint(mx, my):
                    cust_index = (cust_index - 1) % len(COLOR_NAMES)
                elif cust_next_btn.collidepoint(mx, my):
                    cust_index = (cust_index + 1) % len(COLOR_NAMES)
                elif cust_select_btn.collidepoint(mx, my):
                    pick = COLOR_NAMES[cust_index]
                    if pick in unlocked_colors:
                        set_selected_color(pick)
                elif cust_back_btn.collidepoint(mx, my):
                    in_customize = False
            else:
                if resume_btn.collidepoint(mx, my):
                    paused = False
                    reset_survival_timer()
                elif restart_btn.collidepoint(mx, my):
                    restart_game()
                elif settings_btn.collidepoint(mx, my):
                    in_settings = True
                    in_customize = False
                elif customize_btn.collidepoint(mx, my):
                    in_customize = True
                    in_settings = False
                    cust_index = COLOR_NAMES.index(selected_color_name) if selected_color_name in COLOR_NAMES else 0
                elif quit_btn.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()


        # Game over clicks
        if game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            current_w, current_h = window.get_size()
            mx = int(event.pos[0] * (WIDTH / current_w))
            my = int(event.pos[1] * (HEIGHT / current_h))
            if restart_btn.collidepoint(mx, my):
                restart_game()
            elif quit_btn.collidepoint(mx, my):
                pygame.quit()
                sys.exit()

        # Key presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if event.key == pygame.K_e and (not game_over) and (not paused):
                inventory_open = not inventory_open
            if event.key == pygame.K_ESCAPE and not game_over:
                if paused:
                    if in_settings:
                        in_settings = False
                    elif in_customize:
                        in_customize = False
                    else:
                        paused = False
                        reset_survival_timer()
                elif inventory_open:
                    inventory_open = False
                    reset_survival_timer()
                else:
                    paused = True
                    in_settings = False
                    in_customize = False
                    reset_survival_timer()

            # Dash
            if event.key in (pygame.K_LSHIFT, pygame.K_RCTRL) and not game_over and not paused and not inventory_open:
                current_time = pygame.time.get_ticks()
                if current_time - last_dash_time >= dash_cooldown:
                    dash_dx = dash_speed * move_dir
                    # move_and_collide returns 3 values now, but we don't need them for dash
                    move_and_collide(player, dash_dx, 0, platforms + [ground])
                    last_dash_time = current_time

    keys = pygame.key.get_pressed()

    # =========================
    # Pause screen
    # =========================
    if paused:
        screen.fill((135, 206, 235))
        quit_btn = pygame.Rect(btn_x, 580, btn_w, btn_h)

        pygame.draw.rect(screen, (100, 200, 100), pygame.Rect(ground.x, ground.y - camera_y, ground.width, ground.height))

        for plat in platforms:
            pygame.draw.rect(screen, (150, 75, 0), pygame.Rect(plat.x, plat.y - camera_y, plat.width, plat.height))

        for tp in town_platforms:
            pygame.draw.rect(screen, (120, 90, 50), pygame.Rect(tp.x, tp.y - camera_y, tp.width, tp.height))

        for h in houses:
            screen.blit(h["surf"], (h["x"], h["y"] - camera_y))

        for item in world_items:
            draw_rect = pygame.Rect(item["rect"].x, item["rect"].y - camera_y, item["rect"].width, item["rect"].height)
            if item["icon"]:
                screen.blit(item["icon"], draw_rect.topleft)
            else:
                pygame.draw.rect(screen, (255, 215, 0), draw_rect)

        pygame.draw.rect(
            screen,
            COLOR_BY_NAME.get(selected_color_name, (255, 0, 0)),
            pygame.Rect(player.x, player.y - camera_y, player.width, player.height)
        )

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        current_w, current_h = window.get_size()
        raw_mx, raw_my = pygame.mouse.get_pos()
        mx = int(raw_mx * (WIDTH / current_w))
        my = int(raw_my * HEIGHT / current_h)
        mouse_pos = (mx, my)
        
        if in_settings:
            title = big_font.render("SETTINGS", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))

            ctrl_status = "ON" if show_controls else "OFF"
            draw_button(screen, toggle_controls_btn, f"Controls: {ctrl_status}", mouse_pos, font)
            ls_status = "ON" if show_live_score else "OFF"
            draw_button(screen, toggle_live_score_btn, f"Live Score: {ls_status}", mouse_pos, font)
            lvl_status = "ON" if show_lvl else "OFF"
            draw_button(screen, toggle_lvl_btn, f"Level: {lvl_status}", mouse_pos, font)
            draw_button(screen, back_btn, "Back", mouse_pos, font)
        elif in_customize:
            title = big_font.render("CUSTOMIZATION", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))
            name = COLOR_NAMES[cust_index]
            rgb = COLOR_BY_NAME[name]
            needed = UNLOCK_SCORE_BY_NAME[name]
            is_unlocked = name in unlocked_colors
            preview = pygame.Rect(WIDTH // 2 - 60, 245, 120, 120)
            pygame.draw.rect(screen, rgb, preview, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), preview, 3, border_radius= 12)
            label = font.render(name, True, (255, 255, 255))
            screen.blit(label, (WIDTH //2 - label.get_width() // 2, 380))
            if is_unlocked:
                status_text = font.render("Unlocked", True, (180, 255, 180))
            else:
                status_text = font.render(f"Locked (unlock at score {needed})", True, (255, 180, 180))
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, 405))
            draw_button(screen, cust_prev_btn, "< Prev", mouse_pos, font)
            draw_button(screen, cust_next_btn, "Next >", mouse_pos, font)
            select_disabled = not is_unlocked
            select_text = "Selected" if name == selected_color_name else "Select"
            draw_button(screen, cust_select_btn, select_text, mouse_pos, font, disabled=select_disabled)
            draw_button(screen, cust_back_btn, "Back", mouse_pos, font)
        else:
            title = big_font.render("PAUSED", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))

            draw_button(screen, resume_btn, "Resume", mouse_pos, font)
            draw_button(screen, restart_btn, "Restart", mouse_pos, font)
            draw_button(screen, settings_btn, "Settings", mouse_pos, font)
            draw_button(screen, quit_btn, "Quit", mouse_pos, font)
            draw_button(screen, customize_btn, "Customization", mouse_pos, font)

        reset_survival_timer()
        current_w, current_h = window.get_size()
        scaled_surface = pygame.transform.smoothscale(screen, (current_w, current_h))
        window.blit(scaled_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)
        continue

    # =========================
    # Game over screen
    # =========================
    if game_over:
        screen.fill((135, 206, 235))
        quit_btn = pygame.Rect(btn_x, 420, btn_w, btn_h)

        pygame.draw.rect(screen, (100, 200, 100), pygame.Rect(ground.x, ground.y - camera_y, ground.width, ground.height))

        for plat in platforms:
            pygame.draw.rect(screen, (150, 75, 0), pygame.Rect(plat.x, plat.y - camera_y, plat.width, plat.height))

        pygame.draw.rect(screen, COLOR_BY_NAME.get(selected_color_name, (255, 0, 0)), pygame.Rect(player.x, player.y - camera_y, player.width, player.height))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        current_w, current_h = window.get_size()
        raw_mx, raw_my = pygame.mouse.get_pos()
        mx = int(raw_mx * (WIDTH / current_w))
        my = int(raw_my * HEIGHT / current_h)
        mouse_pos = (mx, my)
        if fell:
            title_text = "YOU FELL FROM TOO HIGH"
        elif dead:
            title_text = "YOU DIED"
        else:
            title_text = "GAME OVER"
        title = big_font.render(title_text, True, (255, 155, 155))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        score_line = font.render(f"Score: {score}", True, (255, 255, 255))
        hs_line = font.render(f"High Score: {high_score}", True, (255, 255, 255))
        screen.blit(score_line, (WIDTH // 2 - score_line.get_width() // 2, 230))
        screen.blit(hs_line, (WIDTH // 2 - hs_line.get_width() // 2, 265))

        if new_high:
            new_line = font.render(f"NEW HIGH SCORE! {high_score}", True, (255, 255, 0))
            screen.blit(new_line, (WIDTH // 2 - new_line.get_width() // 2, 305))

        draw_button(screen, restart_btn, "Restart", mouse_pos, font)
        draw_button(screen, quit_btn, "Quit", mouse_pos, font)
        current_w, current_h = window.get_size()
        raw_mx, raw_my = pygame.mouse.get_pos()
        mx = int(raw_mx * (WIDTH / current_w))
        my = int(raw_my * (HEIGHT / current_h))
        scaled_surface=pygame.transform.smoothscale(screen, (current_w, current_h))
        window.blit(scaled_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)
        continue

    # =========================
    # Survival drain
    # =========================
    now = pygame.time.get_ticks()
    dt = (now - last_stat_tick) / 1000.0
    last_stat_tick = now

    food = max(0, food - FOOD_DPS * dt)
    water = max(0, water - WATER_DPS * dt)

    if food <= 0:
        health = max(0, health - STARVE_HDPS * dt)
    if water <= 0:
        health = max(0, health - DEHYDRATE_HDPS * dt)
    
    if health <= 0 and not game_over:
        game_over = True
        dead = True
        fell = False

    # =========================
    # Score update
    # =========================
    if player.y < best_y:
        best_y = player.y
        score = int((ground.top - best_y) / 10)
        update_color_unlocks(score)
        while score >= next_town_score + TOWN_SPAWN_OFFSET:
            spawn_town_at_score(next_town_score)
            next_town_score += TOWN_SCORE_STEP
        if score > high_score:
            high_score = score
            save_high_score(high_score)
            new_high = True
        if score >= ARM_SCORE:
            armed = True
    level = get_level_from_score(score)
    
    # =========================
    # Live Score
    # =========================
    live_score = int((ground.top - player.bottom) / 10)

    # =========================
    # Movement input
    # =========================
    dx = 0
    if not inventory_open:
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
            move_dir = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed
            move_dir = 1

    # =========================
    # Generate platforms above camera
    # =========================
    while highest_plat_y > camera_y - GEN_BUFFER:
        apply_difficulty_for_score(score)
        w = random.randint(PLAT_MIN_W, PLAT_MAX_W)
        gap = random.randint(GAP_MIN_Y, GAP_MAX_Y)
        y = highest_plat_y - gap

        min_x = max(EDGE_MARGIN, last_plat_x - MAX_PLAT_DX)
        max_x = min(WIDTH - EDGE_MARGIN - w, last_plat_x + MAX_PLAT_DX)
        if min_x > max_x:
            min_x = EDGE_MARGIN
            max_x = WIDTH - EDGE_MARGIN - w

        x = random.randint(min_x, max_x)
        platforms.append(pygame.Rect(x, y, w, PLAT_H))

        if random.random() < 0.01:
            item_name = random.choice(VILLAGE_LOOT_POOL)
            item_icon = ITEM_ICONS.get(item_name)
            item_w, item_h = (32, 32)
            if item_icon:
                item_icon = pygame.transform.smoothscale(item_icon, (32, 32))
            item_x = x + (w // 2) - (item_w // 2)
            item_y = y - item_h
            world_items.append({
                "name": item_name,
                "rect": pygame.Rect(item_x, item_y, item_w, item_h),
                "icon": item_icon
            })

        highest_plat_y = y
        last_plat_x = x

    # Remove platforms below camera
    platforms = [p for p in platforms if p.y - camera_y < HEIGHT + DESPAWN_BUFFER]
    town_platforms = [p for p in town_platforms if p.y - camera_y < HEIGHT + DESPAWN_BUFFER]
    world_items = [it for it in world_items if (it["rect"].y - camera_y) <HEIGHT + DESPAWN_BUFFER]

    houses = [
        h for h in houses
        if (h["y"] - camera_y) < HEIGHT + DESPAWN_BUFFER
    ]

    # Ground active / solids list
    ground_active = (ground.y - player.top) < (HEIGHT + 30)
    solids = platforms + town_platforms + ([ground] if ground_active else [])

    # =========================
    # Jump
    # =========================
    if (not inventory_open) and (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and on_ground:
        player_vel_y = jump_power
        on_ground = False

    # Gravity
    player_vel_y += gravity
    dy = player_vel_y

    # =========================
    # Move + collide + detect landings
    # =========================
    was_on_ground = on_ground
    player_vel_y, on_ground, landed_on = move_and_collide(player, dx, dy, solids)
    just_landed = (not was_on_ground) and on_ground

    if was_on_ground and not on_ground:
        fall_peak_y = player.top
    
    if not on_ground:
        if fall_peak_y is None:
            fall_peak_y = player.top
        else:
            fall_peak_y = min(fall_peak_y, player.top)
    
    if just_landed and FALL_DEATH_ENABLED and (not game_over) and (fall_peak_y is not None):
        fall_distance = player.top - fall_peak_y
        if fall_distance >= FALL_DEATH_HEIGHT:
            game_over = True
            fell = True
            dead = False
        fall_peak_y = None
    
    if on_ground:
        fall_peak_y = None

    if DEBUG_LAND_PRINTS and just_landed:
        print("JUST LANDED ON:", "GROUND" if landed_on is ground else "PLATFORM", "score:", score)

    for item in world_items[:]:
        if player.colliderect(item["rect"]):
            if add_item_to_inventory(item["name"], 1):
                world_items.remove(item)

    # =========================
    # Death rules
    # =========================
    # 1) Ground death after score threshold
    if (not game_over) and armed and (live_score <= KILL_SCORE):
        game_over = True
        fell = True
        dead = False

    # =========================
    # Camera
    # =========================
    SCREEN_MID_Y = HEIGHT // 2
    camera_y = player.top - SCREEN_MID_Y
    camera_y = min(camera_y, 0)

    # Walls
    if player.left < 0:
        player.left = 0
    if player.right > WIDTH:
        player.right = WIDTH

    # Dash countdown
    current_time = pygame.time.get_ticks()
    dash_remaining = max(0, dash_cooldown - (current_time - last_dash_time))

    # =========================
    # Drawing
    # =========================
    screen.fill((135, 206, 235))  # sky

    pygame.draw.rect(screen, (100, 200, 100),
                     pygame.Rect(ground.x, ground.y - camera_y, ground.width, ground.height))

    for plat in platforms:
        pygame.draw.rect(screen, (150, 75, 0),
                         pygame.Rect(plat.x, plat.y - camera_y, plat.width, plat.height))

    for tp in town_platforms:
        pygame.draw.rect(
            screen,
            (120, 90, 50),
            pygame.Rect(tp.x, tp.y - camera_y, tp.width, tp.height)
        )
    
    for h in houses:
        screen.blit(h["surf"], (h["x"], h["y"] - camera_y))

    pygame.draw.rect(
        screen,
        COLOR_BY_NAME.get(selected_color_name, (255, 0, 0)),
        pygame.Rect(player.x, player.y - camera_y, player.width, player.height)
    )

    for item in world_items:
        draw_rect = pygame.Rect(item["rect"].x, item["rect"].y - camera_y, item["rect"].width, item["rect"].height)
        if item["icon"]:
            screen.blit(item["icon"], draw_rect.topleft)
        else:
            pygame.draw.rect(screen, (255, 215, 0), draw_rect)

    # Survival HUD
    BAR_W = 260
    BAR_H = 28
    RIGHT_PAD = 20
    TOP_PAD = 20
    GAP = 10

    right_x = WIDTH - RIGHT_PAD

    draw_stat_bar(screen, right_x, TOP_PAD + 0 * (BAR_H + GAP), BAR_W, BAR_H, health,    MAX_STAT, "HP", (220, 60, 60))
    draw_stat_bar(screen, right_x, TOP_PAD + 1 * (BAR_H + GAP), BAR_W, BAR_H, food,    MAX_STAT, "Hunger", (220, 60, 60))
    draw_stat_bar(screen, right_x, TOP_PAD + 2 * (BAR_H + GAP), BAR_W, BAR_H, water,    MAX_STAT, "Thirst", (220, 60, 60))

    # HUD
    live_surf = font.render(f"Live: {live_score}", True, (0, 0, 0))
    lvl_text = font.render(f"Level: {level}", True, (0, 0, 0))
    lvl_x = WIDTH // 2 - lvl_text.get_width() // 2
    lvl_y = 70
    ls_x = WIDTH // 2 - live_surf.get_width() // 2
    ls_y = 105
    
    if show_live_score:
        if show_lvl:
            screen.blit(live_surf, (ls_x, ls_y))
        else:
            screen.blit(live_surf, (ls_x, ls_y - 35))

    if show_lvl:
        screen.blit(lvl_text, (lvl_x, lvl_y))

    score_text = score_font.render(f"Score: {score}", True, (0, 0, 0))
    score_x = WIDTH // 2 - score_text.get_width() // 2
    score_y = 20
    screen.blit(score_text, (score_x, score_y))

    hs_surf = font.render(f"High Score: {high_score}", True, (0, 0, 0))
    screen.blit(hs_surf, (20, HEIGHT - 40))

    inv_slots_rects = None
    if inventory_open:
        inv_slots_rects = draw_inventory(screen, font, selected_slot, inventory)

        current_w, current_h = window.get_size()
        raw_mx, raw_my = pygame.mouse.get_pos()
        mx = int(raw_mx * (WIDTH / current_w))
        my = int(raw_my * (HEIGHT / current_h))
        hover = None
        for i, r in enumerate(inv_slots_rects):
            if r.collidepoint(mx, my):
                hover = i
                break
        selected_slot = hover

    if show_controls:
        controls = [
            "A/<-: move left",
            "D/->: move right",
            "SPACE/W/^: jump",
            "L SHIFT/R CTRL: dash",
            "E: inventory",
            "ESC: pause menu",
        ]
        tx, ty = 20, 20
        line_height = 30
        for i, line in enumerate(controls):
            text_surf = font.render(line, True, (0, 0, 0))
            screen.blit(text_surf, (tx, ty + i * line_height))

    if dash_remaining > 0:
        seconds_left = dash_remaining / 1000
        dash_text = font.render(f"{seconds_left:.1f}", True, (0, 0, 0))
        screen.blit(dash_text, (player.centerx - 15, player.top - camera_y - 20))

    current_w, current_h = window.get_size()
    scaled_surface = pygame.transform.smoothscale(screen, (current_w, current_h))
    window.blit(scaled_surface, (0, 0))

    pygame.display.update()
    clock.tick(60)