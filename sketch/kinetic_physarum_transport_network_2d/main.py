from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5

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

# Internal resolution
W = 1920
H = 1080

NUM_AGENTS = 500000

pos_x = None
pos_y = None
angle = None
grid = None

def setup():
    global pos_x, pos_y, angle, grid
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize agents in a circle
    r = np.random.uniform(0, H//3, NUM_AGENTS)
    theta = np.random.uniform(0, np.pi * 2, NUM_AGENTS)
    pos_x = W / 2 + np.cos(theta) * r
    pos_y = H / 2 + np.sin(theta) * r
    
    # Point inwards
    angle = theta + np.pi + np.random.uniform(-0.5, 0.5, NUM_AGENTS)
    
    grid = np.zeros((H, W), dtype=np.float32)

def read_grid(x, y):
    ix = np.clip(x.astype(np.int32), 0, W-1)
    iy = np.clip(y.astype(np.int32), 0, H-1)
    return grid[iy, ix]

def draw():
    global pos_x, pos_y, angle, grid
    
    # Physarum Hyperparameters
    sensor_angle = np.pi / 4.0
    sensor_dist = 12.0
    turn_speed = np.pi / 8.0
    step_size = 2.0
    deposit_amount = 5.0
    decay_rate = 0.92
    
    # 1. Sense
    s_f_x = pos_x + np.cos(angle) * sensor_dist
    s_f_y = pos_y + np.sin(angle) * sensor_dist
    s_l_x = pos_x + np.cos(angle - sensor_angle) * sensor_dist
    s_l_y = pos_y + np.sin(angle - sensor_angle) * sensor_dist
    s_r_x = pos_x + np.cos(angle + sensor_angle) * sensor_dist
    s_r_y = pos_y + np.sin(angle + sensor_angle) * sensor_dist
    
    w_f = read_grid(s_f_x, s_f_y)
    w_l = read_grid(s_l_x, s_l_y)
    w_r = read_grid(s_r_x, s_r_y)
    
    # 2. Steer
    random_turn = np.random.uniform(-turn_speed, turn_speed, NUM_AGENTS)
    
    mask_f = (w_f > w_l) & (w_f > w_r)
    mask_l = (w_l > w_r) & ~mask_f
    mask_r = (w_r > w_l) & ~mask_f
    mask_eq = (w_l == w_r) & ~mask_f
    
    angle[mask_l] -= turn_speed
    angle[mask_r] += turn_speed
    angle[mask_eq] += random_turn[mask_eq]
    
    # 3. Move
    pos_x += np.cos(angle) * step_size
    pos_y += np.sin(angle) * step_size
    
    # Bounce
    mask_out_x = (pos_x < 0) | (pos_x >= W)
    mask_out_y = (pos_y < 0) | (pos_y >= H)
    pos_x = np.clip(pos_x, 0, W-1)
    pos_y = np.clip(pos_y, 0, H-1)
    
    mask_out = mask_out_x | mask_out_y
    angle[mask_out] = np.random.uniform(0, 2*np.pi, np.sum(mask_out))
    
    # 4. Deposit
    ix = pos_x.astype(np.int32)
    iy = pos_y.astype(np.int32)
    # Fast non-atomic deposit (duplicates are dropped, but it's fine for organic look and much faster)
    grid[iy, ix] += deposit_amount
    
    # 5. Diffuse and Decay
    # 3x3 box blur approximation using 4 adjacent cells + center
    grid_blur = (grid + 
                 np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) + 
                 np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1)) * 0.2
    
    grid = grid_blur * decay_rate
    
    # Map to colors
    # Deep Space Black (#050505) -> Deep Blue (#0033FF) -> Ethereal Green (#00FFAA) -> Toxic Yellow (#CCFF00)
    
    r = np.full((H, W), 5, dtype=np.uint8)
    g = np.full((H, W), 5, dtype=np.uint8)
    b_c = np.full((H, W), 5, dtype=np.uint8)
    
    # Normalized density
    density = grid / 20.0
    density = np.clip(density, 0.0, 1.0)
    
    # Band 1: Black to Blue (0.0 - 0.3)
    m1 = density <= 0.3
    f1 = density[m1] / 0.3
    r[m1] = 5 + (0 - 5) * f1
    g[m1] = 5 + (51 - 5) * f1
    b_c[m1] = 5 + (255 - 5) * f1
    
    # Band 2: Blue to Green (0.3 - 0.7)
    m2 = (density > 0.3) & (density <= 0.7)
    f2 = (density[m2] - 0.3) / 0.4
    r[m2] = 0 + (0 - 0) * f2
    g[m2] = 51 + (255 - 51) * f2
    b_c[m2] = 255 + (170 - 255) * f2
    
    # Band 3: Green to Yellow (0.7 - 1.0)
    m3 = density > 0.7
    f3 = (density[m3] - 0.7) / 0.3
    r[m3] = 0 + (204 - 0) * f3
    g[m3] = 255 + (255 - 255) * f3
    b_c[m3] = 170 + (0 - 170) * f3
    
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    pixels[..., 0] = b_c
    pixels[..., 1] = g
    pixels[..., 2] = r
    pixels[..., 3] = 255
    
    img = py5.create_image_from_numpy(pixels, "ARGB")
    
    # Draw stretched to fill 4K screen
    py5.image(img, 0, 0, py5.width, py5.height)
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
