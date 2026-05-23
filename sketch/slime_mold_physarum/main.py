from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.ndimage import gaussian_filter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Downscale for performance
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2
NUM_AGENTS = 150000

# Agent state
pos_x = np.random.uniform(0, SIM_W, NUM_AGENTS).astype(np.float32)
pos_y = np.random.uniform(0, SIM_H, NUM_AGENTS).astype(np.float32)

# Start in a circle
radius = np.random.uniform(0, min(SIM_W, SIM_H) * 0.4, NUM_AGENTS)
angles = np.random.uniform(0, 2 * np.pi, NUM_AGENTS)
pos_x = SIM_W / 2 + np.cos(angles) * radius
pos_y = SIM_H / 2 + np.sin(angles) * radius

# Angle initially outwards or inward
angle = angles + np.pi # face inwards
speed = 1.0

# Sensor params
sensor_angle = np.pi / 4
sensor_dist = 5.0
turn_speed = 0.5

# Pheromone map
trail_map = np.zeros((SIM_H, SIM_W), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos_x, pos_y, angle, trail_map
    
    # 1. Sense phase
    # Sensor positions
    fl_x = pos_x + np.cos(angle + sensor_angle) * sensor_dist
    fl_y = pos_y + np.sin(angle + sensor_angle) * sensor_dist
    
    f_x = pos_x + np.cos(angle) * sensor_dist
    f_y = pos_y + np.sin(angle) * sensor_dist
    
    fr_x = pos_x + np.cos(angle - sensor_angle) * sensor_dist
    fr_y = pos_y + np.sin(angle - sensor_angle) * sensor_dist
    
    # Wrap sensors
    fl_x = np.clip(fl_x, 0, SIM_W - 1).astype(int)
    fl_y = np.clip(fl_y, 0, SIM_H - 1).astype(int)
    f_x = np.clip(f_x, 0, SIM_W - 1).astype(int)
    f_y = np.clip(f_y, 0, SIM_H - 1).astype(int)
    fr_x = np.clip(fr_x, 0, SIM_W - 1).astype(int)
    fr_y = np.clip(fr_y, 0, SIM_H - 1).astype(int)
    
    # Sense pheromone
    weight_fl = trail_map[fl_y, fl_x]
    weight_f  = trail_map[f_y, f_x]
    weight_fr = trail_map[fr_y, fr_x]
    
    # Steer
    # If forward is greatest, stay. If FL > FR, steer left. If FR > FL, steer right.
    # If FL == FR but both > F, pick randomly
    rnd = np.random.rand(NUM_AGENTS)
    
    steer = np.zeros(NUM_AGENTS, dtype=np.float32)
    
    # F is biggest
    mask_f = (weight_f > weight_fl) & (weight_f > weight_fr)
    # FL is biggest
    mask_fl = (weight_fl > weight_f) & (weight_fl > weight_fr)
    # FR is biggest
    mask_fr = (weight_fr > weight_f) & (weight_fr > weight_fl)
    
    # Random steering
    mask_rand = (weight_fl == weight_fr) & (weight_fl > weight_f)
    
    steer[mask_fl] = turn_speed
    steer[mask_fr] = -turn_speed
    
    # For random mask
    steer_rand = np.where(rnd > 0.5, turn_speed, -turn_speed)
    steer[mask_rand] = steer_rand[mask_rand]
    
    angle += steer
    
    # Move
    pos_x += np.cos(angle) * speed
    pos_y += np.sin(angle) * speed
    
    # Bounce off walls
    bounce_x = (pos_x < 0) | (pos_x >= SIM_W)
    bounce_y = (pos_y < 0) | (pos_y >= SIM_H)
    
    pos_x = np.clip(pos_x, 0, SIM_W - 1)
    pos_y = np.clip(pos_y, 0, SIM_H - 1)
    
    angle[bounce_x] = np.pi - angle[bounce_x]
    angle[bounce_y] = -angle[bounce_y]
    
    # Add some random walk
    angle += (np.random.rand(NUM_AGENTS) - 0.5) * 0.1
    
    # 2. Deposit phase
    px = pos_x.astype(int)
    py_ = pos_y.astype(int)
    
    # Vectorized deposit: use np.add.at for overlapping agents
    np.add.at(trail_map, (py_, px), 1.0)
    
    # 3. Diffuse & Decay phase
    # Scipy gaussian_filter for fast diffusion
    trail_map = gaussian_filter(trail_map, sigma=1.0)
    
    # Decay
    trail_map *= 0.95
    
    # Render
    # Map trail_map (0 to ~2.0) to color
    # Base: Black. Trail: Deep Violet to Electric Green
    norm_trail = np.clip(trail_map, 0.0, 1.0)
    
    # 2x nearest-neighbor upscale to screen size
    r_up = np.kron(norm_trail, np.ones((2, 2), dtype=np.float32))
    r_up = r_up[:SIZE[1], :SIZE[0]]
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Electric Green: (0, 255, 100)
    # Deep Violet: (100, 0, 200)
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = (100 * r_up * (1-r_up)*2 + 0 * r_up).astype(np.uint8)
    pixels[:, :, 2] = (0 * r_up * (1-r_up)*2 + 255 * r_up).astype(np.uint8)
    pixels[:, :, 3] = (200 * r_up * (1-r_up)*2 + 100 * r_up).astype(np.uint8)
    
    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
