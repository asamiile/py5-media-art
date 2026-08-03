from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import copy
import numpy as np

import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840x2160

# ---  Simulation Constants ---
SIM_W, SIM_H = 960, 540  # Simulation space (rendered at 1/4 resolution, upscaled)
N_FOOD = 20
MAX_CREATURES = 400
N_SENSORS = 15
N_HIDDEN = 10
HEALTH_DECAY = 0.18
SENSOR_RANGE = 60.0        # How far sensors reach (in simulation space)
EAT_RADIUS = 14.0
FOOD_RADIUS = 22.0
REPRODUCE_PROB = 0.0006
MUTATION_RATE = 0.12
MAX_SPEED = 1.6

# --- Color palettes (in HSB) ---
PALETTE = {
    "bg": (2, 3, 5),               # Near black obsidian
    "food": (45, 220, 255),        # Solar amber
    "healthy": (175, 255, 240),    # Aquamarine / bioluminescent teal
    "mid": (280, 200, 200),        # Violet mid-health
    "dying": (350, 255, 230),      # Crimson / red low-health
    "sensor_on": (60, 200, 255),   # Yellow-white sensor glow
    "sensor_off": (200, 60, 60),   # Dim blue sensor line
}

# HUD layout areas (in sim coords)
HUD_X = SIM_W - 200
HUD_Y = 20

creatures = []
food_items = []
population_history = []
birth_count = 0
death_count = 0
generation_avg_health = []
pimg = None   # Py5Image buffer for blit (avoids Retina DPI mismatch)


# ========== Neural Network ==========
class NeuralNetwork:
    """Tiny feedforward 3-layer NN: (N_SENSORS) -> (N_HIDDEN) -> 2."""

    def __init__(self):
        # Xavier-initialized weights
        self.w1 = np.random.randn(N_HIDDEN, N_SENSORS) * math.sqrt(2.0 / N_SENSORS)
        self.b1 = np.zeros(N_HIDDEN)
        self.w2 = np.random.randn(2, N_HIDDEN) * math.sqrt(2.0 / N_HIDDEN)
        self.b2 = np.zeros(2)

    def feedforward(self, inputs: np.ndarray) -> np.ndarray:
        h = 1.0 / (1.0 + np.exp(-np.clip(self.w1 @ inputs + self.b1, -20, 20)))
        out = 1.0 / (1.0 + np.exp(-np.clip(self.w2 @ h + self.b2, -20, 20)))
        return out

    def copy(self) -> "NeuralNetwork":
        nn = NeuralNetwork.__new__(NeuralNetwork)
        nn.w1 = self.w1.copy()
        nn.b1 = self.b1.copy()
        nn.w2 = self.w2.copy()
        nn.b2 = self.b2.copy()
        return nn

    def mutate(self, rate: float = MUTATION_RATE):
        mask1 = np.random.rand(*self.w1.shape) < rate
        self.w1 += mask1 * np.random.randn(*self.w1.shape) * 0.15
        mask_b1 = np.random.rand(*self.b1.shape) < rate
        self.b1 += mask_b1 * np.random.randn(*self.b1.shape) * 0.15
        mask2 = np.random.rand(*self.w2.shape) < rate
        self.w2 += mask2 * np.random.randn(*self.w2.shape) * 0.15
        mask_b2 = np.random.rand(*self.b2.shape) < rate
        self.b2 += mask_b2 * np.random.randn(*self.b2.shape) * 0.15


# ========== Creature ==========
class Creature:
    def __init__(self, x, y, brain=None, hue=None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.health = 100.0
        self.brain = brain.copy() if brain else NeuralNetwork()
        # Genetic hue — inherited with slight drift for lineage coloring
        self.hue = hue if hue is not None else random.uniform(140, 200)
        self.sensor_values = np.zeros(N_SENSORS)
        self.sensor_angles = [2 * math.pi * i / N_SENSORS for i in range(N_SENSORS)]

    def sense(self, food_list):
        """Build sensor vector: each sensor fires if food within range in that direction."""
        self.sensor_values[:] = 0.0
        for f in food_list:
            dx, dy = f.x - self.x, f.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist >= SENSOR_RANGE * 2:
                continue
            # Check each sensor's directional activation
            for i, ang in enumerate(self.sensor_angles):
                sx = math.cos(ang) * SENSOR_RANGE
                sy = math.sin(ang) * SENSOR_RANGE
                # Distance from sensor tip to food
                tip_dx = (self.x + sx) - f.x
                tip_dy = (self.y + sy) - f.y
                tip_dist = math.sqrt(tip_dx * tip_dx + tip_dy * tip_dy)
                if tip_dist < f.radius:
                    activation = max(0.0, 1.0 - tip_dist / f.radius)
                    self.sensor_values[i] = max(self.sensor_values[i], activation)

    def update(self, food_list, creatures_list):
        global birth_count, death_count
        
        self.sense(food_list)
        
        # Neural network decides angle and magnitude of force
        out = self.brain.feedforward(self.sensor_values)
        angle = out[0] * 2.0 * math.pi
        magnitude = out[1] * 0.8 + 0.05  # 0.05-0.85 magnitude
        
        ax = math.cos(angle) * magnitude
        ay = math.sin(angle) * magnitude
        
        self.vx += ax * 0.3
        self.vy += ay * 0.3
        
        # Cap speed
        spd = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        if spd > MAX_SPEED:
            self.vx = self.vx / spd * MAX_SPEED
            self.vy = self.vy / spd * MAX_SPEED
        
        self.x += self.vx
        self.y += self.vy
        
        # Toroidal wrap-around
        self.x = self.x % SIM_W
        self.y = self.y % SIM_H
        
        # Eat food
        for f in food_list:
            dx, dy = f.x - self.x, f.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < EAT_RADIUS + f.radius:
                gain = min(f.energy, 8.0)
                self.health = min(self.health + gain, 150.0)
                f.energy -= gain * 0.5
        
        # Passive health drain
        self.health -= HEALTH_DECAY
        
        # Reproduce stochastically
        if self.health > 60 and random.random() < REPRODUCE_PROB and len(creatures_list) < MAX_CREATURES:
            child_brain = self.brain.copy()
            child_brain.mutate()
            child_hue = (self.hue + random.gauss(0, 5)) % 360
            child = Creature(self.x + random.gauss(0, 8), self.y + random.gauss(0, 8), child_brain, child_hue)
            child.health = self.health * 0.45
            self.health *= 0.55
            creatures_list.append(child)
            birth_count += 1

    @property
    def alive(self):
        return self.health > 0


# ========== Food ==========
class Food:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else random.uniform(30, SIM_W - 30)
        self.y = y if y is not None else random.uniform(30, SIM_H - 30)
        self.energy = random.uniform(40, 100)
        self.radius = FOOD_RADIUS
    
    def update(self):
        # Gently drift
        self.x += random.gauss(0, 0.1)
        self.y += random.gauss(0, 0.1)
        self.x = max(10, min(SIM_W - 10, self.x))
        self.y = max(10, min(SIM_H - 10, self.y))
        # Slowly regenerate energy
        self.energy = min(self.energy + 0.05, 100)


def replenish_food():
    """Keep food count at target level."""
    while len(food_items) < N_FOOD:
        food_items.append(Food())
    # Remove exhausted food
    for i in range(len(food_items) - 1, -1, -1):
        if food_items[i].energy < 5:
            food_items[i] = Food()


def setup():
    global creatures, food_items, pimg
    
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # CPU-heap image buffer (avoids Retina DPI issues)
    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)
    
    # Initialize creatures
    for _ in range(80):
        c = Creature(random.uniform(50, SIM_W - 50), random.uniform(50, SIM_H - 50))
        creatures.append(c)
    
    # Initialize food
    for _ in range(N_FOOD):
        food_items.append(Food())


def draw_sim_to_buffer():
    """Render simulation into a NumPy ARGB array, then blit into pimg."""
    # Create ARGB canvas array
    canvas = np.zeros((SIM_H, SIM_W, 4), dtype=np.uint8)
    
    # Background: obsidian
    bg = PALETTE["bg"]
    bgr, bgg, bgb = hsb_to_rgb(bg[0], bg[1], bg[2])
    canvas[:, :, 0] = int(bgg)    # G channel (ARGB layout: A,R,G,B)
    # Actually let's use ARGB: channel 0=A, 1=R, 2=G, 3=B
    canvas[:, :, 0] = 255
    canvas[:, :, 1] = bgr
    canvas[:, :, 2] = bgg
    canvas[:, :, 3] = bgb
    
    # Draw food pellets
    for f in food_items:
        draw_circle_on_canvas(canvas, int(f.x), int(f.y), int(f.radius),
                               45, 200, int(f.energy * 2.5), alpha=200)
        # Glow halo
        draw_circle_on_canvas(canvas, int(f.x), int(f.y), int(f.radius) + 6,
                               45, 150, int(f.energy * 1.5), alpha=80)
    
    # Draw creatures
    for c in creatures:
        hp_ratio = max(0, min(1, c.health / 100.0))
        
        # Health-based hue: teal (healthy) → violet → crimson (dying)
        if hp_ratio > 0.5:
            # Healthy: full hue
            h = c.hue
            s = int(200 + hp_ratio * 55)
            v = int(180 + hp_ratio * 75)
        else:
            # Dying: hue shifts toward red (350)
            h = c.hue + (1 - hp_ratio * 2) * (350 - c.hue)
            s = 255
            v = int(180 + hp_ratio * 60)
        
        h = int(h) % 360
        creature_r = max(3, int(6 + hp_ratio * 10))
        
        # Sensor rays
        for i, ang in enumerate(c.sensor_angles):
            sv = c.sensor_values[i]
            ex = int(c.x + math.cos(ang) * SENSOR_RANGE * 0.8)
            ey = int(c.y + math.sin(ang) * SENSOR_RANGE * 0.8)
            # Clamp to canvas
            x0, y0 = int(c.x), int(c.y)
            if sv > 0.3:
                draw_line_on_canvas(canvas, x0, y0, ex, ey, 45, 180, 255, alpha=int(sv * 120))
            else:
                draw_line_on_canvas(canvas, x0, y0, ex, ey, 200, 60, 60, alpha=25)
        
        # Glow halo
        draw_circle_on_canvas(canvas, int(c.x), int(c.y), creature_r + 5, h, s, v, alpha=50)
        # Body
        draw_circle_on_canvas(canvas, int(c.x), int(c.y), creature_r, h, s, v, alpha=230)
    
    return canvas


def hsb_to_rgb(h, s, b):
    """Convert HSB (0-360, 0-255, 0-255) to RGB (0-255)."""
    h = (h % 360) / 360.0
    s = s / 255.0
    b = b / 255.0
    
    if s == 0:
        r = g = bl = b
    else:
        i = int(h * 6)
        f = h * 6 - i
        p = b * (1 - s)
        q = b * (1 - f * s)
        t = b * (1 - (1 - f) * s)
        i %= 6
        if i == 0: r, g, bl = b, t, p
        elif i == 1: r, g, bl = q, b, p
        elif i == 2: r, g, bl = p, b, t
        elif i == 3: r, g, bl = p, q, b
        elif i == 4: r, g, bl = t, p, b
        else: r, g, bl = b, p, q
    return int(r * 255), int(g * 255), int(bl * 255)


def draw_circle_on_canvas(canvas, cx, cy, radius, h, s, v, alpha=255):
    """Draw a filled anti-aliased circle on the ARGB numpy canvas."""
    H, W = canvas.shape[:2]
    r = max(1, radius)
    x0 = max(0, cx - r - 1)
    x1 = min(W, cx + r + 2)
    y0 = max(0, cy - r - 1)
    y1 = min(H, cy + r + 2)
    
    if x0 >= x1 or y0 >= y1:
        return
    
    cr, cg, cb = hsb_to_rgb(h, s, v)
    
    ys, xs = np.mgrid[y0:y1, x0:x1]
    dists = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    mask = dists <= r
    
    if not np.any(mask):
        return
    
    # Alpha blend with existing canvas
    a_frac = alpha / 255.0
    existing_a = canvas[y0:y1, x0:x1, 0][mask] / 255.0
    
    canvas[y0:y1, x0:x1, 0][mask] = 255
    canvas[y0:y1, x0:x1, 1][mask] = np.clip(
        canvas[y0:y1, x0:x1, 1][mask] * (1 - a_frac) + cr * a_frac, 0, 255
    ).astype(np.uint8)
    canvas[y0:y1, x0:x1, 2][mask] = np.clip(
        canvas[y0:y1, x0:x1, 2][mask] * (1 - a_frac) + cg * a_frac, 0, 255
    ).astype(np.uint8)
    canvas[y0:y1, x0:x1, 3][mask] = np.clip(
        canvas[y0:y1, x0:x1, 3][mask] * (1 - a_frac) + cb * a_frac, 0, 255
    ).astype(np.uint8)


def draw_line_on_canvas(canvas, x0, y0, x1, y1, h, s, v, alpha=150):
    """Draw a 1px line on canvas using Bresenham's algorithm."""
    H, W = canvas.shape[:2]
    cr, cg, cb = hsb_to_rgb(h, s, v)
    a_frac = alpha / 255.0
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    steps = 0
    while steps < 200:  # Safety cap
        if 0 <= x0 < W and 0 <= y0 < H:
            canvas[y0, x0, 0] = 255
            canvas[y0, x0, 1] = int(canvas[y0, x0, 1] * (1 - a_frac) + cr * a_frac)
            canvas[y0, x0, 2] = int(canvas[y0, x0, 2] * (1 - a_frac) + cg * a_frac)
            canvas[y0, x0, 3] = int(canvas[y0, x0, 3] * (1 - a_frac) + cb * a_frac)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
        steps += 1


def draw():
    global creatures, food_items, birth_count, death_count, population_history
    
    fc = py5.frame_count
    
    # --- Simulation step ---
    replenish_food()
    for f in food_items:
        f.update()
    
    # Update creatures, remove dead
    for c in creatures:
        c.update(food_items, creatures)
    
    dead_this_frame = sum(1 for c in creatures if not c.alive)
    death_count += dead_this_frame
    creatures = [c for c in creatures if c.alive]
    
    # Record population for history plot
    if fc % 5 == 0:
        population_history.append(len(creatures))
        if len(population_history) > 200:
            population_history.pop(0)
    
    # --- Render simulation to numpy buffer ---
    canvas = draw_sim_to_buffer()
    
    # Blit into Py5Image  
    pimg.load_pixels()
    argb_flat = (
        (canvas[:, :, 0].astype(np.int32) << 24)
        | (canvas[:, :, 1].astype(np.int32) << 16)
        | (canvas[:, :, 2].astype(np.int32) << 8)
        | canvas[:, :, 3].astype(np.int32)
    )
    pimg.pixels[:] = argb_flat.flatten()
    pimg.update_pixels()
    
    # --- Draw to 4K canvas ---
    py5.background(2, 3, 5)
    py5.image(pimg, 0, 0, py5.width, py5.height)
    
    # --- HUD overlay in 4K space ---
    scale_x = py5.width / SIM_W
    scale_y = py5.height / SIM_H
    hud_panel_x = int(HUD_X * scale_x)
    hud_panel_y = int(HUD_Y * scale_y)
    panel_w = int(190 * scale_x)
    panel_h = int(200 * scale_y)
    
    # HUD background panel
    py5.no_stroke()
    py5.fill(0, 0, 8, 210)
    py5.rect(hud_panel_x, hud_panel_y, panel_w, panel_h, 8)
    
    # HUD border
    py5.stroke(175, 200, 200, 160)
    py5.stroke_weight(1.5)
    py5.no_fill()
    py5.rect(hud_panel_x, hud_panel_y, panel_w, panel_h, 8)
    
    # HUD title
    py5.no_stroke()
    py5.fill(175, 200, 255)
    txt_scale = scale_x * 0.9
    py5.text_size(int(12 * txt_scale))
    py5.text("NEUROEVOLUTION ECOSYSTEM", hud_panel_x + 10, hud_panel_y + 20)
    
    # Stats
    py5.text_size(int(10 * txt_scale))
    py5.fill(175, 150, 200)
    py5.text(f"Population: {len(creatures):>4d}", hud_panel_x + 10, hud_panel_y + 44)
    py5.text(f"Births:     {birth_count:>4d}", hud_panel_x + 10, hud_panel_y + 62)
    py5.text(f"Deaths:     {death_count:>4d}", hud_panel_x + 10, hud_panel_y + 80)
    py5.text(f"Food:       {len(food_items):>4d}", hud_panel_x + 10, hud_panel_y + 98)
    if creatures:
        avg_health = np.mean([c.health for c in creatures])
        py5.text(f"Avg Health: {avg_health:>5.1f}", hud_panel_x + 10, hud_panel_y + 116)
    
    # Population history sparkline
    py5.text_size(int(9 * txt_scale))
    py5.fill(175, 120, 160)
    py5.text("Population History", hud_panel_x + 10, hud_panel_y + 142)
    
    if len(population_history) > 2:
        sp_x = hud_panel_x + 10
        sp_y = hud_panel_y + panel_h - 20
        sp_w = panel_w - 20
        sp_h = int(50 * scale_y)
        
        max_pop = max(1, max(population_history))
        min_pop = min(population_history)
        
        py5.stroke(175, 200, 200, 120)
        py5.stroke_weight(1.5)
        py5.no_fill()
        py5.begin_shape()
        for i, pop in enumerate(population_history):
            x = sp_x + int(i / len(population_history) * sp_w)
            y = sp_y - int((pop - min_pop) / max(1, max_pop - min_pop) * sp_h)
            py5.vertex(x, y)
        py5.end_shape()
    
    # Frame counter / progress bar
    progress = fc / TOTAL_FRAMES
    bar_y = int(py5.height - 30 * scale_y)
    bar_w = py5.width
    bar_h = int(4 * scale_y)
    py5.no_stroke()
    py5.fill(0, 0, 30)
    py5.rect(0, bar_y, bar_w, bar_h)
    py5.fill(175, 255, 220)
    py5.rect(0, bar_y, int(bar_w * progress), bar_h)
    
    # Work name watermark
    py5.fill(175, 80, 160, 120)
    py5.text_size(int(9 * txt_scale))
    py5.text(WORK_NAME, int(10 * scale_x), int(py5.height - 10 * scale_y))
    
    # Fail-safe: abort if nothing visible
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {fc}. Aborting.")
            import os
            os._exit(1)
    
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | Pop: {len(creatures)}")
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Preview: copy middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
        
        import os
        os._exit(0)


py5.run_sketch()
