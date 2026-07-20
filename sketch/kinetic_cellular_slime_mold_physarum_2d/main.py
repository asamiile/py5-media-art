from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Slime mold simulation grid (lower res for performance)
GRID_SCALE = 4
GRID_W = SIZE[0] // GRID_SCALE
GRID_H = SIZE[1] // GRID_SCALE

# Chemical trail grid
trail = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Agent settings
NUM_AGENTS = 50000
SENSOR_DIST = 9
SENSOR_ANGLE = np.pi / 4.0
TURN_SPEED = 0.2
MOVE_SPEED = 1.0

# Agent states
agents_x = np.random.uniform(0, GRID_W, NUM_AGENTS)
agents_y = np.random.uniform(0, GRID_H, NUM_AGENTS)

# Start agents pointing towards center to create a collapsing star effect
center_x = GRID_W / 2
center_y = GRID_H / 2
agents_angle = np.arctan2(center_y - agents_y, center_x - agents_x) + np.random.uniform(-0.1, 0.1, NUM_AGENTS)

def diffuse_and_decay(grid, decay_rate=0.95):
    # Quick 3x3 box blur using numpy array shifting
    # Pad to handle edges
    padded = np.pad(grid, 1, mode='wrap')
    
    # Sum of 3x3 neighborhood
    blurred = (
        padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
        padded[1:-1, :-2] + padded[1:-1, 1:-1] + padded[1:-1, 2:] +
        padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
    ) / 9.0
    
    return blurred * decay_rate

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global agents_x, agents_y, agents_angle, trail
    
    # 1. Sense
    # Calculate sensor positions (Left, Forward, Right)
    sense_f_x = np.clip((agents_x + np.cos(agents_angle) * SENSOR_DIST).astype(int), 0, GRID_W - 1)
    sense_f_y = np.clip((agents_y + np.sin(agents_angle) * SENSOR_DIST).astype(int), 0, GRID_H - 1)
    
    sense_l_x = np.clip((agents_x + np.cos(agents_angle - SENSOR_ANGLE) * SENSOR_DIST).astype(int), 0, GRID_W - 1)
    sense_l_y = np.clip((agents_y + np.sin(agents_angle - SENSOR_ANGLE) * SENSOR_DIST).astype(int), 0, GRID_H - 1)
    
    sense_r_x = np.clip((agents_x + np.cos(agents_angle + SENSOR_ANGLE) * SENSOR_DIST).astype(int), 0, GRID_W - 1)
    sense_r_y = np.clip((agents_y + np.sin(agents_angle + SENSOR_ANGLE) * SENSOR_DIST).astype(int), 0, GRID_H - 1)
    
    # Read chemical levels
    weight_f = trail[sense_f_y, sense_f_x]
    weight_l = trail[sense_l_y, sense_l_x]
    weight_r = trail[sense_r_y, sense_r_x]
    
    # Random steering factor to prevent locking
    random_steer = np.random.uniform(-0.1, 0.1, NUM_AGENTS)
    
    # Turn logic
    # If forward is best, stay same (plus random).
    # If left and right are both better than forward, turn randomly.
    # Otherwise, turn towards the best.
    
    turn_left_mask = (weight_l > weight_f) & (weight_l > weight_r)
    turn_right_mask = (weight_r > weight_f) & (weight_r > weight_l)
    turn_random_mask = (weight_l > weight_f) & (weight_r > weight_f) & (weight_l == weight_r)
    
    agents_angle[turn_left_mask] -= TURN_SPEED
    agents_angle[turn_right_mask] += TURN_SPEED
    
    # Randomly pick left or right if both are equal and better than forward
    rand_choice = np.random.choice([-TURN_SPEED, TURN_SPEED], NUM_AGENTS)
    agents_angle[turn_random_mask] += rand_choice[turn_random_mask]
    
    # Add base random steering to everyone
    agents_angle += random_steer
    
    # 2. Move
    agents_x += np.cos(agents_angle) * MOVE_SPEED
    agents_y += np.sin(agents_angle) * MOVE_SPEED
    
    # Wrap around edges (torus topology)
    agents_x = agents_x % GRID_W
    agents_y = agents_y % GRID_H
    
    # 3. Deposit
    # Convert to int coordinates for grid deposit
    ax_int = agents_x.astype(int)
    ay_int = agents_y.astype(int)
    
    # Accumulate trail using bincount for speed (since multiple agents can be on the same cell)
    # flattened index: y * W + x
    flat_indices = ay_int * GRID_W + ax_int
    deposits = np.bincount(flat_indices, minlength=GRID_W * GRID_H)
    trail += deposits.reshape((GRID_H, GRID_W)) * 2.0
    
    # 4. Diffuse and Decay
    # Very slight decay, very high diffusion for slime mold
    trail = diffuse_and_decay(trail, decay_rate=0.92)
    
    # 5. Render
    # We will map the numpy array `trail` to a py5 image directly
    # trail is between 0 and some max value. We map this to color.
    py5.background(0)
    
    # Normalize trail for display
    t_max = np.max(trail)
    if t_max > 0:
        normalized = np.clip(trail / (t_max * 0.5), 0, 1) # overdrive it a bit
    else:
        normalized = trail
        
    # We want toxic green (hue ~100) and yellow (hue ~60) on purple background
    # Since writing directly to pixels is complicated due to ARGB conversion,
    # we'll draw it using points, but only where trail > threshold to be fast
    
    y_coords, x_coords = np.nonzero(normalized > 0.05)
    intensities = normalized[y_coords, x_coords]
    
    py5.no_stroke()
    py5.stroke_weight(GRID_SCALE * 1.5)
    py5.blend_mode(py5.ADD)
    
    # Draw points (we have to loop, but only over active pixels)
    # This is fast enough for < 100k active pixels
    for i in range(len(x_coords)):
        x = x_coords[i]
        y = y_coords[i]
        inte = intensities[i]
        
        hue = 280.0 - (float(inte) * 180.0)
        brightness = float(inte) * 100.0
        py5.stroke(hue, 100, brightness, 90)
        py5.point(float(x * GRID_SCALE), float(y * GRID_SCALE))

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

py5.run_sketch()
