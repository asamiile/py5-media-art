from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.signal import convolve2d

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
W, H = SIZE

# Flocking Parameters
NUM_BOIDS = 250000
GRID_RES = 256
MAX_SPEED = 12.0
DT = 0.5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, kernel, colormap
    
    # Init boids
    pos = np.random.uniform(0, 1, (NUM_BOIDS, 2)).astype(np.float32)
    pos[:, 0] *= W
    pos[:, 1] *= H
    
    ang = np.random.uniform(0, 2*np.pi, NUM_BOIDS)
    vel = np.column_stack((np.cos(ang), np.sin(ang))).astype(np.float32) * MAX_SPEED
    
    # Smoothing kernel for mean-field grid
    kernel = np.ones((7, 7), dtype=np.float32)
    
    # Starling Murmuration Colormap (Cyan -> Deep Blue -> Magenta -> Bright Pink/White)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        val = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if val < 0.2:
            p = val / 0.2
            colormap[i, 1:] = [0, int(200 - p*150), int(255 - p*100)] # Cyan to Blue
        elif val < 0.6:
            p = (val - 0.2) / 0.4
            colormap[i, 1:] = [int(p * 200), int(50 - p*50), int(155 + p*100)] # Blue to Magenta
        else:
            p = (val - 0.6) / 0.4
            colormap[i, 1:] = [200 + int(p * 55), int(p * 255), 255] # Magenta to Pink/White

def step_physics(t):
    global pos, vel
    
    # 1. Discretize into Grid
    grid_x = ((pos[:, 0] / W) * GRID_RES).astype(np.int32) % GRID_RES
    grid_y = ((pos[:, 1] / H) * GRID_RES).astype(np.int32) % GRID_RES
    
    count = np.zeros((GRID_RES, GRID_RES), dtype=np.float32)
    np.add.at(count, (grid_y, grid_x), 1.0)
    
    sum_px = np.zeros((GRID_RES, GRID_RES), dtype=np.float32)
    np.add.at(sum_px, (grid_y, grid_x), pos[:, 0])
    
    sum_py = np.zeros((GRID_RES, GRID_RES), dtype=np.float32)
    np.add.at(sum_py, (grid_y, grid_x), pos[:, 1])
    
    sum_vx = np.zeros((GRID_RES, GRID_RES), dtype=np.float32)
    np.add.at(sum_vx, (grid_y, grid_x), vel[:, 0])
    
    sum_vy = np.zeros((GRID_RES, GRID_RES), dtype=np.float32)
    np.add.at(sum_vy, (grid_y, grid_x), vel[:, 1])
    
    # 2. Smooth grids
    c_count = convolve2d(count, kernel, mode='same', boundary='wrap') + 1e-5
    c_px = convolve2d(sum_px, kernel, mode='same', boundary='wrap') / c_count
    c_py = convolve2d(sum_py, kernel, mode='same', boundary='wrap') / c_count
    c_vx = convolve2d(sum_vx, kernel, mode='same', boundary='wrap') / c_count
    c_vy = convolve2d(sum_vy, kernel, mode='same', boundary='wrap') / c_count
    
    # Gradient of density for separation
    sep_y, sep_x = np.gradient(c_count)
    
    # 3. Flocking Forces
    f_align_x = c_vx[grid_y, grid_x] - vel[:, 0]
    f_align_y = c_vy[grid_y, grid_x] - vel[:, 1]
    
    # Correct cohesion for periodic boundaries
    # Instead of wrapping just the force, we approximate:
    dx_cohes = c_px[grid_y, grid_x] - pos[:, 0]
    dy_cohes = c_py[grid_y, grid_x] - pos[:, 1]
    dx_cohes = dx_cohes - W * np.round(dx_cohes / W)
    dy_cohes = dy_cohes - H * np.round(dy_cohes / H)
    
    f_separ_x = -sep_x[grid_y, grid_x]
    f_separ_y = -sep_y[grid_y, grid_x]
    
    vel[:, 0] += (f_align_x * 0.08 + dx_cohes * 0.02 + f_separ_x * 0.05) * DT
    vel[:, 1] += (f_align_y * 0.08 + dy_cohes * 0.02 + f_separ_y * 0.05) * DT
    
    # 4. Predator Forces
    # 3 predators flying in smooth Lissajous curves
    for i in range(3):
        px = W/2 + np.cos(t * 0.7 + i * 2.0) * (W * 0.4)
        py = H/2 + np.sin(t * 0.5 + i * 2.0) * (H * 0.4)
        
        dx = pos[:, 0] - px
        dy = pos[:, 1] - py
        # wrap
        dx = dx - W * np.round(dx / W)
        dy = dy - H * np.round(dy / H)
        
        dist_sq = dx**2 + dy**2 + 100.0
        # Flee force
        force = 50000.0 / (dist_sq + 10.0)
        vel[:, 0] += dx * force * DT
        vel[:, 1] += dy * force * DT
    
    # 5. Add a gentle vortex/noise field to keep them moving organically
    vel[:, 0] += np.sin(pos[:, 1] * 0.01 + t) * 0.5
    vel[:, 1] += np.cos(pos[:, 0] * 0.01 - t) * 0.5
    
    # 6. Normalize velocity
    speed = np.hypot(vel[:, 0], vel[:, 1]) + 1e-5
    
    # Soft speed limit
    desired_speed = np.where(speed > MAX_SPEED, MAX_SPEED, speed)
    desired_speed = np.where(desired_speed < MAX_SPEED * 0.3, MAX_SPEED * 0.3, desired_speed)
    
    vel[:, 0] = (vel[:, 0] / speed) * desired_speed
    vel[:, 1] = (vel[:, 1] / speed) * desired_speed
    
    # 7. Update Position
    pos[:, 0] = (pos[:, 0] + vel[:, 0] * DT) % W
    pos[:, 1] = (pos[:, 1] + vel[:, 1] * DT) % H
    
    # Store local density for coloring
    global boid_density
    boid_density = c_count[grid_y, grid_x]

def draw():
    global pos, vel, boid_density
    
    t = py5.frame_count * 0.05
    step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 220 // 256).astype(np.uint8)
    
    # Color boids based on local density
    normalized_density = np.clip(boid_density / 50.0, 0.0, 1.0)
    color_indices = (normalized_density * 255).astype(np.uint8)
    
    sx = pos[:, 0].astype(np.int32)
    sy = pos[:, 1].astype(np.int32)
    
    valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx = sx[valid]
    sy = sy[valid]
    c_idx = color_indices[valid]
    
    colors = colormap[c_idx]
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    np.add.at(flat_pixels[:, 1], flat_indices, colors[:, 1])
    np.add.at(flat_pixels[:, 2], flat_indices, colors[:, 2])
    np.add.at(flat_pixels[:, 3], flat_indices, colors[:, 3])
    
    # Clamp to 255
    flat_pixels[:, 1:] = np.clip(flat_pixels[:, 1:], 0, 255)
    
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
