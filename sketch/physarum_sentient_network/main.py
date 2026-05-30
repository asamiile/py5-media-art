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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Physarum Parameters
N_AGENTS = 800000
SA = np.pi / 8      # Sensor angle
SO = 12             # Sensor offset
RA = np.pi / 4      # Rotation angle
STEP = 3.5
DECAY = 0.90
DEPOSIT = 10.0

positions = None
angles = None
pheromone = None
lut = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions, angles, pheromone, lut
    W, H = py5.width, py5.height
    
    # Initialize agents in a dense cluster
    r_dist = np.random.rand(N_AGENTS) ** 0.5 * (min(W, H) * 0.4)
    theta = np.random.rand(N_AGENTS) * 2 * np.pi
    
    positions = np.column_stack((
        W/2 + np.cos(theta) * r_dist,
        H/2 + np.sin(theta) * r_dist
    ))
    angles = theta + (np.random.rand(N_AGENTS) - 0.5) * np.pi
    
    pheromone = np.zeros((H, W), dtype=np.float32)
    
    lut = np.zeros((256, 4), dtype=np.uint8)
    py5.color_mode(py5.RGB, 255)
    for i in range(256):
        if i < 40:
            t = i / 40.0
            r = int(5 + t * (5 - 5))
            g = int(5 + t * (15 - 5))
            b = int(10 + t * (80 - 10))
        elif i < 100:
            t = (i - 40) / 60.0
            r = int(5 + t * (20 - 5))
            g = int(15 + t * (50 - 15))
            b = int(80 + t * (200 - 80))
        elif i < 180:
            t = (i - 100) / 80.0
            r = int(20 + t * (120 - 20))
            g = int(50 + t * (200 - 50))
            b = int(200 + t * (240 - 200))
        else:
            t = (i - 180) / 75.0
            r = int(120 + t * (255 - 120))
            g = int(200 + t * (50 - 200))
            b = int(240 + t * (150 - 240))
        lut[i] = [255, r, g, b]

def draw():
    global positions, angles, pheromone
    
    W, H = py5.width, py5.height
    
    angles_left = angles - SA
    angles_right = angles + SA
    
    px = positions[:, 0]
    py = positions[:, 1]
    
    def sense(a):
        sx = np.clip((px + np.cos(a) * SO).astype(int), 0, W - 1)
        sy = np.clip((py + np.sin(a) * SO).astype(int), 0, H - 1)
        return pheromone[sy, sx]
        
    weight_f = sense(angles)
    weight_l = sense(angles_left)
    weight_r = sense(angles_right)
    
    r_turn = np.random.rand(N_AGENTS)
    random_turn = (weight_f < weight_l) & (weight_f < weight_r)
    turn_left = (weight_l > weight_r) & ~random_turn
    turn_right = (weight_r > weight_l) & ~random_turn
    random_l = random_turn & (r_turn < 0.5)
    random_r = random_turn & (r_turn >= 0.5)
    
    angles[turn_left | random_l] -= RA * (0.8 + 0.4 * np.random.rand((turn_left | random_l).sum()))
    angles[turn_right | random_r] += RA * (0.8 + 0.4 * np.random.rand((turn_right | random_r).sum()))
    
    positions[:, 0] += np.cos(angles) * STEP
    positions[:, 1] += np.sin(angles) * STEP
    
    positions[:, 0] = positions[:, 0] % W
    positions[:, 1] = positions[:, 1] % H
    
    ix = positions[:, 0].astype(int)
    iy = positions[:, 1].astype(int)
    linear_indices = iy * W + ix
    counts = np.bincount(linear_indices, minlength=W*H)
    pheromone += counts.reshape((H, W)) * DEPOSIT
    
    pheromone_clipped = np.clip(pheromone, 0, 255).astype(np.uint8)
    py5.load_np_pixels()
    py5.np_pixels[:] = lut[pheromone_clipped]
    py5.update_np_pixels()
    
    pheromone = gaussian_filter(pheromone, sigma=1.0) * DECAY
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
