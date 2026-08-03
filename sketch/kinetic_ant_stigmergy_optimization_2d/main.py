from pathlib import Path
import shutil
import subprocess
import sys
import math
import random
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

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Offscreen simulation grid (960x540 has 16x fewer pixels than 4K)
SIM_W, SIM_H = 960, 540

# Ant Colony Parameters
NUM_ANTS = 800  # Optimized number of agents for rich density and fast simulation
NUM_FOOD = 5
DECAY = 0.985  # Slightly adjusted evaporation rate for faster dynamics
DIFFUSE_RATE = 0.15  # Diffusion rate
DEPOSIT_HOME = 35.0
DEPOSIT_FOOD = 45.0
SENSOR_DIST = 16.0
SENSOR_ANGLE = math.radians(35)
TURN_SPEED = math.radians(28)  # Wider angle for quick response
SPEED = 3.6  # Faster speed to compensate for single step per frame

HIVE_X, HIVE_Y = SIM_W / 2.0, SIM_H / 2.0
HIVE_RADIUS_SIM = 15.0
FOOD_RADIUS_SIM = 12.0

# Pheromone Grids
pheromone_home = np.zeros((SIM_H, SIM_W), dtype=np.float32)
pheromone_food = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Entities
class FoodSource:
    def __init__(self, angle_offset, distance, initial_amount=800.0):
        self.angle_offset = angle_offset
        self.distance = distance
        self.amount = initial_amount
        self.max_amount = initial_amount
        self.x = 0.0
        self.y = 0.0

    def update_position(self, fc):
        # Slow orbital rotation around the hive
        theta = self.angle_offset + fc * 0.002
        self.x = HIVE_X + math.cos(theta) * self.distance
        self.y = HIVE_Y + math.sin(theta) * self.distance

foods = []
food_gathered = 0
pg = None

# Vectorized Ant Swarm State Arrays
ant_x = np.zeros(NUM_ANTS, dtype=np.float32)
ant_y = np.zeros(NUM_ANTS, dtype=np.float32)
ant_angle = np.zeros(NUM_ANTS, dtype=np.float32)
ant_has_food = np.zeros(NUM_ANTS, dtype=bool)
ant_trail_strength = np.ones(NUM_ANTS, dtype=np.float32)

def update_simulation(fc):
    global food_gathered, pheromone_home, pheromone_food
    global ant_x, ant_y, ant_angle, ant_has_food, ant_trail_strength

    # Update Food Source Positions
    for food in foods:
        food.update_position(fc)

    # 1. Pheromone sensing for all ants (Vectorized)
    # Compute sensor coordinates
    l_angle = ant_angle - SENSOR_ANGLE
    c_angle = ant_angle
    r_angle = ant_angle + SENSOR_ANGLE

    lx = (ant_x + np.cos(l_angle) * SENSOR_DIST).astype(np.int32) % SIM_W
    ly = (ant_y + np.sin(l_angle) * SENSOR_DIST).astype(np.int32) % SIM_H
    cx = (ant_x + np.cos(c_angle) * SENSOR_DIST).astype(np.int32) % SIM_W
    cy = (ant_y + np.sin(c_angle) * SENSOR_DIST).astype(np.int32) % SIM_H
    rx = (ant_x + np.cos(r_angle) * SENSOR_DIST).astype(np.int32) % SIM_W
    ry = (ant_y + np.sin(r_angle) * SENSOR_DIST).astype(np.int32) % SIM_H

    # Sample grids (sample both food and home pheromones to keep it vectorized)
    l_food = pheromone_food[ly, lx]
    l_home = pheromone_home[ly, lx]
    l_vals = np.where(ant_has_food, l_home, l_food)

    c_food = pheromone_food[cy, cx]
    c_home = pheromone_home[cy, cx]
    c_vals = np.where(ant_has_food, c_home, c_food)

    r_food = pheromone_food[ry, rx]
    r_home = pheromone_home[ry, rx]
    r_vals = np.where(ant_has_food, r_home, r_food)

    # 2. Vectorized steering logic
    go_straight = (c_vals > l_vals) & (c_vals > r_vals)
    turn_left = (l_vals > r_vals) & ~go_straight
    turn_right = (r_vals > l_vals) & ~go_straight
    random_turn = (l_vals == r_vals) & ~go_straight

    steer = np.zeros(NUM_ANTS, dtype=np.float32)
    steer[turn_left] = -TURN_SPEED
    steer[turn_right] = TURN_SPEED
    
    # For random turning states, apply random uniform angles
    num_random = np.sum(random_turn)
    if num_random > 0:
        steer[random_turn] = np.random.uniform(-TURN_SPEED, TURN_SPEED, size=num_random)

    # Add general chaotic wander
    steer += np.random.uniform(-0.12, 0.12, size=NUM_ANTS)
    ant_angle = (ant_angle + steer) % math.tau

    # 3. Vectorized movement
    ant_x = (ant_x + np.cos(ant_angle) * SPEED) % SIM_W
    ant_y = (ant_y + np.sin(ant_angle) * SPEED) % SIM_H

    # Integer grid coordinates
    gx = ant_x.astype(np.int32) % SIM_W
    gy = ant_y.astype(np.int32) % SIM_H

    # 4. Deposit pheromones (using fast numpy add.at for vector accumulation)
    carrying = ant_has_food
    searching = ~ant_has_food

    if np.any(carrying):
        np.add.at(pheromone_food, (gy[carrying], gx[carrying]), DEPOSIT_FOOD * ant_trail_strength[carrying])
        # Slowly decay carrying ant's trail strength as it travels further
        ant_trail_strength[carrying] = np.maximum(0.2, ant_trail_strength[carrying] - 0.005)

    if np.any(searching):
        np.add.at(pheromone_home, (gy[searching], gx[searching]), DEPOSIT_HOME)

    # Global boundary clipping to prevent saturation
    pheromone_home = np.clip(pheromone_home, 0, 255.0)
    pheromone_food = np.clip(pheromone_food, 0, 255.0)

    # 5. Check food pickup interactions (vectorized for all searching ants)
    for food in foods:
        if food.amount > 0:
            dists = np.hypot(ant_x - food.x, ant_y - food.y)
            pickup = (dists < FOOD_RADIUS_SIM) & (food.amount > 0) & searching
            num_pickups = np.sum(pickup)
            if num_pickups > 0:
                ant_has_food[pickup] = True
                ant_trail_strength[pickup] = 1.0
                ant_angle[pickup] += math.pi  # Turn around to return to hive
                food.amount = max(0.0, food.amount - num_pickups)

    # 6. Check hive return interactions (vectorized for all carrying ants)
    dists_hive = np.hypot(ant_x - HIVE_X, ant_y - HIVE_Y)
    reached_hive = (dists_hive < HIVE_RADIUS_SIM) & carrying
    num_hive_returns = np.sum(reached_hive)
    if num_hive_returns > 0:
        ant_has_food[reached_hive] = False
        ant_angle[reached_hive] += math.pi  # Turn back to search again
        food_gathered += num_hive_returns

    # 7. Vectorized pheromone diffusion & evaporation
    def diffuse(grid):
        left = np.roll(grid, -1, axis=1)
        right = np.roll(grid, 1, axis=1)
        up = np.roll(grid, -1, axis=0)
        down = np.roll(grid, 1, axis=0)
        blurred = (1.0 - DIFFUSE_RATE) * grid + (DIFFUSE_RATE / 4.0) * (left + right + up + down)
        return blurred * DECAY

    pheromone_home = diffuse(pheromone_home)
    pheromone_food = diffuse(pheromone_food)

def setup():
    global pg, foods, ant_x, ant_y, ant_angle, ant_has_food, ant_trail_strength
    py5.size(*SIZE)
    py5.smooth(4)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Create offscreen buffer as a standard Py5Image to bypass Retina auto-scaling shape mismatches
    pg = py5.create_image(SIM_W, SIM_H, py5.ARGB)

    # Initialize Ants (Vectorized NumPy arrays)
    random.seed(1337)
    np.random.seed(1337)
    ant_x = np.full(NUM_ANTS, HIVE_X, dtype=np.float32) + np.random.uniform(-5, 5, size=NUM_ANTS)
    ant_y = np.full(NUM_ANTS, HIVE_Y, dtype=np.float32) + np.random.uniform(-5, 5, size=NUM_ANTS)
    ant_angle = np.random.uniform(0, math.tau, size=NUM_ANTS).astype(np.float32)
    ant_has_food = np.zeros(NUM_ANTS, dtype=bool)
    ant_trail_strength = np.ones(NUM_ANTS, dtype=np.float32)

    # Initialize Food Sources in a beautiful pentagram orbit
    angles = [i * (math.tau / NUM_FOOD) for i in range(NUM_FOOD)]
    distances = [180.0, 240.0, 210.0, 260.0, 200.0]
    for a, d in zip(angles, distances):
        foods.append(FoodSource(a, d))

def draw():
    global pheromone_home, pheromone_food
    fc = py5.frame_count

    # 1. Update Simulation
    # Run 1 step per frame with compensated speed for maximum performance
    update_simulation(fc)

    # 2. Render Pheromone Trails and Ants to Py5Image Buffer
    pg.load_np_pixels()

    # Color Mapping:
    # Home trail: warm solar gold/orange (R=255, G=125, B=15)
    # Food trail: electric cyan/blue (R=0, G=220, B=255)
    # Deep obsidian background: R=10, G=8, B=13
    h_intensity = np.clip(pheromone_home * 1.6, 0, 255)
    f_intensity = np.clip(pheromone_food * 2.2, 0, 255)

    r_ch = np.clip(10 + h_intensity * 1.0 + f_intensity * 0.0, 0, 255).astype(np.uint8)
    g_ch = np.clip(8 + h_intensity * 0.49 + f_intensity * 0.86, 0, 255).astype(np.uint8)
    b_ch = np.clip(13 + h_intensity * 0.06 + f_intensity * 1.0, 0, 255).astype(np.uint8)

    # Draw Ants directly into channels (cyan if empty, orange/gold if carrying)
    xs = ant_x.astype(np.int32) % SIM_W
    ys = ant_y.astype(np.int32) % SIM_H

    # Make ants 2x2 pixels on SIM buffer (scales to 8x8 in 4K) for strong visibility
    for dx in [0, 1]:
        for dy in [0, 1]:
            cur_xs = (xs + dx) % SIM_W
            cur_ys = (ys + dy) % SIM_H

            # Set food carrying ants to gold (R=255, G=180, B=30)
            r_ch[cur_ys[ant_has_food], cur_xs[ant_has_food]] = 255
            g_ch[cur_ys[ant_has_food], cur_xs[ant_has_food]] = 180
            b_ch[cur_ys[ant_has_food], cur_xs[ant_has_food]] = 30

            # Set searching ants to cyan (R=0, G=240, B=255)
            r_ch[cur_ys[~ant_has_food], cur_xs[~ant_has_food]] = 0
            g_ch[cur_ys[~ant_has_food], cur_xs[~ant_has_food]] = 240
            b_ch[cur_ys[~ant_has_food], cur_xs[~ant_has_food]] = 255

    # Assign channels (Py5Image is guaranteed 960x540 on all systems, bypassing Retina scales)
    pg.np_pixels[..., 0] = r_ch
    pg.np_pixels[..., 1] = g_ch
    pg.np_pixels[..., 2] = b_ch
    pg.np_pixels[..., 3] = 255  # Opaque

    pg.update_np_pixels()

    # 3. Blit upscaled pheromone buffer to 4K canvas
    py5.image(pg, 0, 0, py5.width, py5.height)

    # 4. Draw Hive & Food Sources in 4K
    scale_x = py5.width / SIM_W
    scale_y = py5.height / SIM_H

    # Hive (Central Nest)
    hive_4k_x = HIVE_X * scale_x
    hive_4k_y = HIVE_Y * scale_y
    hive_rad_4k = HIVE_RADIUS_SIM * scale_x

    py5.no_fill()
    py5.stroke(255, 176, 31, 60)
    py5.stroke_weight(3)
    py5.circle(hive_4k_x, hive_4k_y, hive_rad_4k * 2.5)

    py5.fill(255, 176, 31, 210)
    py5.no_stroke()
    py5.circle(hive_4k_x, hive_4k_y, hive_rad_4k * 1.8)

    # Food Sources
    for i, food in enumerate(foods):
        fx = food.x * scale_x
        fy = food.y * scale_y
        frad = FOOD_RADIUS_SIM * scale_x * (food.amount / food.max_amount)

        if food.amount > 0:
            # Bioluminescent glow
            py5.no_fill()
            py5.stroke(0, 230, 118, 50)
            py5.stroke_weight(2)
            py5.circle(fx, fy, frad * 2.8)

            py5.fill(0, 230, 118, 190)
            py5.no_stroke()
            py5.circle(fx, fy, frad * 1.8)

            # Draw food index label
            py5.fill(255, 230)
            py5.text_size(14)
            py5.text(f"F-{i+1}", fx - 10, fy - frad * 2.0)

    # 6. Technical Telemetry HUD
    # Outer frame
    py5.stroke(0, 229, 255, 80)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.rect(40, 40, py5.width - 80, py5.height - 80)

    # Outer tick lines
    py5.stroke(0, 229, 255, 180)
    py5.stroke_weight(3)
    py5.line(30, 40, 50, 40)
    py5.line(40, 30, 40, 50)
    py5.line(py5.width - 30, 40, py5.width - 50, 40)
    py5.line(py5.width - 40, 30, py5.width - 40, 50)
    py5.line(30, py5.height - 40, 50, py5.height - 40)
    py5.line(40, py5.height - 30, 40, py5.height - 50)
    py5.line(py5.width - 30, py5.height - 40, py5.width - 50, py5.height - 40)
    py5.line(py5.width - 40, py5.height - 30, py5.width - 40, py5.height - 50)

    # Telemetry data text block (left side)
    py5.fill(0, 229, 255, 230)
    py5.text_size(24)
    py5.text("SYSTEM: DECEN. SWARM PATHFINDING", 80, 100)
    py5.text_size(18)
    py5.fill(255, 220)
    py5.text(f"AGENT POPULATION : {NUM_ANTS} ACTIVE", 80, 140)
    py5.text(f"RESOURCE NODES   : {sum(1 for f in foods if f.amount > 0)} / {NUM_FOOD}", 80, 170)
    py5.text(f"COLLECTED MATTER : {food_gathered} UNITS", 80, 200)

    total_ph = float(pheromone_home.sum() + pheromone_food.sum()) / (SIM_W * SIM_H)
    py5.text(f"STIGMERGY VALUE  : {total_ph:.4f} ρ/px", 80, 230)

    # Progress bar (right side)
    bar_width = 300
    bar_x = py5.width - 80 - bar_width
    bar_y = 90
    py5.no_fill()
    py5.stroke(0, 229, 255, 100)
    py5.stroke_weight(2)
    py5.rect(bar_x, bar_y, bar_width, 16)
    py5.fill(0, 229, 255, 180)
    py5.no_stroke()
    py5.rect(bar_x + 2, bar_y + 2, (bar_width - 4) * (fc / TOTAL_FRAMES), 12)

    py5.fill(255, 220)
    py5.text(f"FRAME RENDER : {fc} / {TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)", bar_x, bar_y - 15)

    # Fail-safe blank screen detection
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {fc} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot (convert final snapshot to PNG as required)
        mid_frame = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.jpg")
        subprocess.run(["ffmpeg", "-y", "-i", mid_frame, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)

py5.run_sketch()
