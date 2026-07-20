from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.signal import convolve2d

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

# Physarum simulation parameters
GRID_SCALE = 3
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

NUM_PARTICLES = 300000

# Particle state: x, y, angle
# Initialize in a circle looking inwards
theta = np.random.rand(NUM_PARTICLES).astype(np.float32) * 2 * np.pi
r = np.random.rand(NUM_PARTICLES).astype(np.float32) * (min(ROWS, COLS) * 0.4)
cx, cy = COLS / 2, ROWS / 2
px = (cx + r * np.cos(theta)).astype(np.float32)
py = (cy + r * np.sin(theta)).astype(np.float32)
# Angle towards center + noise
p_angle = (np.arctan2(cy - py, cx - px) + (np.random.rand(NUM_PARTICLES) - 0.5) * 0.5).astype(np.float32)

trail_map = np.zeros((ROWS, COLS), dtype=np.float32)

# Sensor params
sensor_angle = np.pi / 4
sensor_dist = 5.0
turn_speed = np.pi / 8
move_speed = 1.0

# Diffusion kernel
kernel = np.array([
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 1]
], dtype=np.float32) / 9.0
decay = 0.9

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global px, py, p_angle, trail_map
    
    # We step the simulation multiple times per frame
    for _ in range(2):
        # 1. Sense
        s_left_x = px + np.cos(p_angle + sensor_angle) * sensor_dist
        s_left_y = py + np.sin(p_angle + sensor_angle) * sensor_dist
        s_mid_x = px + np.cos(p_angle) * sensor_dist
        s_mid_y = py + np.sin(p_angle) * sensor_dist
        s_right_x = px + np.cos(p_angle - sensor_angle) * sensor_dist
        s_right_y = py + np.sin(p_angle - sensor_angle) * sensor_dist
        
        # wrap coords
        s_left_x = np.mod(s_left_x, COLS).astype(np.int32)
        s_left_y = np.mod(s_left_y, ROWS).astype(np.int32)
        s_mid_x = np.mod(s_mid_x, COLS).astype(np.int32)
        s_mid_y = np.mod(s_mid_y, ROWS).astype(np.int32)
        s_right_x = np.mod(s_right_x, COLS).astype(np.int32)
        s_right_y = np.mod(s_right_y, ROWS).astype(np.int32)
        
        # Read trail map
        # using integer array indexing
        val_left = trail_map[s_left_y, s_left_x]
        val_mid = trail_map[s_mid_y, s_mid_x]
        val_right = trail_map[s_right_y, s_right_x]
        
        # 2. Turn
        # if mid > left and mid > right: go straight (no turn)
        # if mid < left and mid < right: turn randomly left or right
        # if left > right: turn left
        # if right > left: turn right
        random_steer = (np.random.rand(NUM_PARTICLES).astype(np.float32) - 0.5) * 2.0
        
        turn = np.zeros(NUM_PARTICLES, dtype=np.float32)
        
        mask_random = (val_mid < val_left) & (val_mid < val_right)
        mask_left = (val_left > val_right) & ~mask_random
        mask_right = (val_right > val_left) & ~mask_random
        
        turn[mask_random] = random_steer[mask_random] * turn_speed
        turn[mask_left] = turn_speed
        turn[mask_right] = -turn_speed
        
        p_angle += turn
        
        # 3. Move
        px += np.cos(p_angle) * move_speed
        py += np.sin(p_angle) * move_speed
        
        # Wrap coords
        px = np.mod(px, COLS)
        py = np.mod(py, ROWS)
        
        # 4. Deposit
        # To avoid loops, we use np.add.at which safely adds to repeated indices
        p_xi = px.astype(np.int32)
        p_yi = py.astype(np.int32)
        np.add.at(trail_map, (p_yi, p_xi), 5.0)
        
        # 5. Diffuse & Decay
        trail_map = convolve2d(trail_map, kernel, mode='same', boundary='wrap') * decay
        trail_map = np.clip(trail_map, 0, 255)
        
    # Render
    py5.load_np_pixels()
    
    # Palette: Deep purple, golden yellow, magenta
    # trail map is ~0 to 255
    v = trail_map / 255.0
    
    r_out = v**0.5 * 255 + (1-v) * 20
    g_out = v * 200 + (1-v) * 5
    b_out = v**2 * 50 + (1-v) * 40
    
    r_out = np.clip(r_out, 0, 255).astype(np.uint8)
    g_out = np.clip(g_out, 0, 255).astype(np.uint8)
    b_out = np.clip(b_out, 0, 255).astype(np.uint8)
    
    # Upscale
    r_scaled = np.kron(r_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    g_scaled = np.kron(g_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    b_scaled = np.kron(b_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    
    # Crop to screen
    r_scaled = r_scaled[:py5.height, :py5.width]
    g_scaled = g_scaled[:py5.height, :py5.width]
    b_scaled = b_scaled[:py5.height, :py5.width]
    
    # In py5, np_pixels is shape (height, width, 4) in ARGB format on Mac
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r_scaled # Red
    py5.np_pixels[:, :, 2] = g_scaled # Green
    py5.np_pixels[:, :, 3] = b_scaled # Blue
    
    py5.update_np_pixels()

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
