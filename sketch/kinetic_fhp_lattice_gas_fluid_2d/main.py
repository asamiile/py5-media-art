from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# FHP Simulation parameters
SIM_W = 480
SIM_H = 270

# Hexagonal unit directions
DIRS = np.array([
    [1.0, 0.0],                        # 0: Right
    [0.5, np.sqrt(3)/2],               # 1: Down-Right (row increases downwards)
    [-0.5, np.sqrt(3)/2],              # 2: Down-Left
    [-1.0, 0.0],                       # 3: Left
    [-0.5, -np.sqrt(3)/2],             # 4: Up-Left
    [0.5, -np.sqrt(3)/2]               # 5: Up-Right
])

# Initialize lattice gas grid: boolean array of shape (6, H, W)
grid = np.zeros((6, SIM_H, SIM_W), dtype=bool)

# Create circular cylinder obstacle
obstacle = np.zeros((SIM_H, SIM_W), dtype=bool)
cy, cx = SIM_H // 2, SIM_W // 4
r_cylinder = 22
y_indices, x_indices = np.ogrid[:SIM_H, :SIM_W]
obstacle[(x_indices - cx)**2 + (y_indices - cy)**2 <= r_cylinder**2] = True

# Seed initial state with moving flow and some noise
grid[0, :, :] = True  # Inflow particles moving right
# Add random thermal noise
grid[:, :, :] |= (np.random.random(grid.shape) < 0.15)
# Ensure no particles inside obstacle
grid[:, obstacle] = False

# Tracer particles for visualization
num_tracers = 8000
tracers = np.zeros((num_tracers, 2))
tracers[:, 0] = np.random.random(num_tracers) * (SIM_W - 2) + 1
tracers[:, 1] = np.random.random(num_tracers) * (SIM_H - 2) + 1
tracer_colors = np.random.random(num_tracers)  # Random hues or variations

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def propagate():
    global grid
    new_grid = np.zeros_like(grid)
    
    # 0: Right (r, c+1)
    new_grid[0] = np.roll(grid[0], shift=1, axis=1)
    # 3: Left (r, c-1)
    new_grid[3] = np.roll(grid[3], shift=-1, axis=1)
    
    # Diagonal directions require handling even and odd rows separately
    # 1: Down-Right. Even rows shift to (r+1, c). Odd rows shift to (r+1, c+1)
    # 2: Down-Left. Even rows shift to (r+1, c-1). Odd rows shift to (r+1, c)
    # 4: Up-Left. Even rows shift to (r-1, c-1). Odd rows shift to (r-1, c)
    # 5: Up-Right. Even rows shift to (r-1, c). Odd rows shift to (r-1, c+1)
    
    # Create mask for even/odd rows
    even_mask = np.arange(SIM_H) % 2 == 0
    odd_mask = ~even_mask
    
    # Upwards propagation (axis 0 shifted by -1)
    rolled_up = np.roll(grid, shift=-1, axis=1) # shifts rows up (r-1)
    
    # 5: Up-Right. Even rows shift (r-1, c). Odd rows shift (r-1, c+1)
    new_grid[5, even_mask, :] = rolled_up[5, even_mask, :]
    new_grid[5, odd_mask, :] = np.roll(rolled_up[5, odd_mask, :], shift=1, axis=1)
    
    # 4: Up-Left. Even rows shift (r-1, c-1). Odd rows shift (r-1, c)
    new_grid[4, even_mask, :] = np.roll(rolled_up[4, even_mask, :], shift=-1, axis=1)
    new_grid[4, odd_mask, :] = rolled_up[4, odd_mask, :]
    
    # Downwards propagation (axis 0 shifted by +1)
    rolled_down = np.roll(grid, shift=1, axis=1) # shifts rows down (r+1)
    
    # 1: Down-Right. Even rows shift (r+1, c). Odd rows shift (r+1, c+1)
    new_grid[1, even_mask, :] = rolled_down[1, even_mask, :]
    new_grid[1, odd_mask, :] = np.roll(rolled_down[1, odd_mask, :], shift=1, axis=1)
    
    # 2: Down-Left. Even rows shift (r+1, c-1). Odd rows shift (r+1, c)
    new_grid[2, even_mask, :] = np.roll(rolled_down[2, even_mask, :], shift=-1, axis=1)
    new_grid[2, odd_mask, :] = rolled_down[2, odd_mask, :]
    
    grid = new_grid

def collide():
    global grid
    n0, n1, n2, n3, n4, n5 = grid[0], grid[1], grid[2], grid[3], grid[4], grid[5]
    
    # 3-body collision masks
    three_body_1 = n0 & n2 & n4 & ~n1 & ~n3 & ~n5
    three_body_2 = n1 & n3 & n5 & ~n0 & ~n2 & ~n4
    
    n0[three_body_1], n2[three_body_1], n4[three_body_1] = False, False, False
    n1[three_body_1], n3[three_body_1], n5[three_body_1] = True, True, True
    
    n1[three_body_2], n3[three_body_2], n5[three_body_2] = False, False, False
    n0[three_body_2], n2[three_body_2], n4[three_body_2] = True, True, True
    
    # 2-body collision masks (head-on). Must not have other particles present.
    pair_03 = n0 & n3 & ~n1 & ~n2 & ~n4 & ~n5
    pair_14 = n1 & n4 & ~n0 & ~n2 & ~n3 & ~n5
    pair_25 = n2 & n5 & ~n0 & ~n1 & ~n3 & ~n4
    
    rand_mask = np.random.random(SIM_H * SIM_W).reshape(SIM_H, SIM_W) < 0.5
    
    # pair 03 scatters to 14 or 25
    scatter_03_to_14 = pair_03 & rand_mask
    scatter_03_to_25 = pair_03 & ~rand_mask
    n0[pair_03], n3[pair_03] = False, False
    n1[scatter_03_to_14], n4[scatter_03_to_14] = True, True
    n2[scatter_03_to_25], n5[scatter_03_to_25] = True, True
    
    # pair 14 scatters to 03 or 25
    scatter_14_to_03 = pair_14 & rand_mask
    scatter_14_to_25 = pair_14 & ~rand_mask
    n1[pair_14], n4[pair_14] = False, False
    n0[scatter_14_to_03], n3[scatter_14_to_03] = True, True
    n2[scatter_14_to_25], n5[scatter_14_to_25] = True, True
    
    # pair 25 scatters to 03 or 14
    scatter_25_to_03 = pair_25 & rand_mask
    scatter_25_to_14 = pair_25 & ~rand_mask
    n2[pair_25], n5[pair_25] = False, False
    n0[scatter_25_to_03], n3[scatter_25_to_03] = True, True
    n1[scatter_25_to_14], n4[scatter_25_to_14] = True, True

def handle_boundaries():
    global grid
    n0, n1, n2, n3, n4, n5 = grid[0], grid[1], grid[2], grid[3], grid[4], grid[5]
    
    obs_n0, obs_n1, obs_n2, obs_n3, obs_n4, obs_n5 = (
        n0[obstacle], n1[obstacle], n2[obstacle], n3[obstacle], n4[obstacle], n5[obstacle]
    )
    
    n0[obstacle], n3[obstacle] = obs_n3, obs_n0
    n1[obstacle], n4[obstacle] = obs_n4, obs_n1
    n2[obstacle], n5[obstacle] = obs_n5, obs_n2
    
    t_n1, t_n2, t_n4, t_n5 = grid[1, 0, :], grid[2, 0, :], grid[4, 0, :], grid[5, 0, :]
    grid[1, 0, :], grid[5, 0, :] = t_n5, t_n1
    grid[2, 0, :], grid[4, 0, :] = t_n4, t_n2
    
    b_n1, b_n2, b_n4, b_n5 = grid[1, SIM_H-1, :], grid[2, SIM_H-1, :], grid[4, SIM_H-1, :], grid[5, SIM_H-1, :]
    grid[1, SIM_H-1, :], grid[5, SIM_H-1, :] = b_n5, b_n1
    grid[2, SIM_H-1, :], grid[4, SIM_H-1, :] = b_n4, b_n2

    grid[0, :, 0] = True
    grid[3, :, 0] = False
    grid[0, :, 1:5] |= (np.random.random((SIM_H, 4)) < 0.45)
    grid[:, :, SIM_W-1] = False

def get_smoothed_fields():
    density = np.sum(grid, axis=0, dtype=float)
    
    velocity = np.zeros((2, SIM_H, SIM_W))
    for i in range(6):
        velocity[0] += grid[i] * DIRS[i, 0]
        velocity[1] += grid[i] * DIRS[i, 1]
        
    smoothed_d = np.copy(density)
    smoothed_vx = np.copy(velocity[0])
    smoothed_vy = np.copy(velocity[1])
    
    for shift in [-2, -1, 1, 2]:
        smoothed_d += np.roll(density, shift, axis=0) + np.roll(density, shift, axis=1)
        smoothed_vx += np.roll(velocity[0], shift, axis=0) + np.roll(velocity[0], shift, axis=1)
        smoothed_vy += np.roll(velocity[1], shift, axis=0) + np.roll(velocity[1], shift, axis=1)
        
    smoothed_d /= 9.0
    smoothed_vx /= 9.0
    smoothed_vy /= 9.0
    
    return smoothed_d, smoothed_vx, smoothed_vy

def draw():
    global tracers
    
    for _ in range(3):
        propagate()
        collide()
        handle_boundaries()
        
    smoothed_d, smoothed_vx, smoothed_vy = get_smoothed_fields()
    
    py5.load_np_pixels()
    h_screen, w_screen = SIZE[1], SIZE[0]
    
    norm_d = np.clip(smoothed_d / 4.0, 0.0, 1.0)
    
    rgb_buf = np.zeros((SIM_H, SIM_W, 3), dtype=np.uint8)
    rgb_buf[:, :, 0] = (norm_d * 40).astype(np.uint8)
    rgb_buf[:, :, 1] = (norm_d * 120).astype(np.uint8)
    rgb_buf[:, :, 2] = (norm_d * 180).astype(np.uint8)
    rgb_buf[obstacle] = 10
    
    pimg = py5.create_image(SIM_W, SIM_H, py5.RGB)
    pimg.load_pixels()
    r = rgb_buf[:, :, 0].astype(np.int32)
    g = rgb_buf[:, :, 1].astype(np.int32)
    b = rgb_buf[:, :, 2].astype(np.int32)
    a = np.ones_like(r) * 255
    argb = (a << 24) | (r << 16) | (g << 8) | b
    pimg.pixels[:] = argb.flatten()
    pimg.update_pixels()
    
    py5.image(pimg, 0, 0, w_screen, h_screen)
    
    py5.no_stroke()
    py5.fill(0, 0, 0, 40)
    py5.rect(0, 0, w_screen, h_screen)
    
    py5.stroke_weight(2.0)
    py5.stroke(255)
    
    scale_x = w_screen / SIM_W
    scale_y = h_screen / SIM_H
    
    tx = tracers[:, 0]
    ty = tracers[:, 1]
    
    ix = np.clip(tx.astype(int), 0, SIM_W - 1)
    iy = np.clip(ty.astype(int), 0, SIM_H - 1)
    
    vx = smoothed_vx[iy, ix]
    vy = smoothed_vy[iy, ix]
    
    tx += vx * 1.5 + 0.4
    ty += vy * 1.5
    
    offscreen = (tx >= SIM_W - 1) | (tx < 1) | (ty >= SIM_H - 1) | (ty < 1)
    hit_obs = obstacle[np.clip(ty.astype(int), 0, SIM_H - 1), np.clip(tx.astype(int), 0, SIM_W - 1)]
    reset_mask = offscreen | hit_obs
    
    tx[reset_mask] = 1.0
    ty[reset_mask] = np.random.random(np.sum(reset_mask)) * (SIM_H - 2) + 1
    
    tracers[:, 0] = tx
    tracers[:, 1] = ty
    
    speeds = np.sqrt(vx**2 + vy**2)
    norm_speeds = np.clip(speeds / 1.5, 0.0, 1.0)
    
    # Fast rendering: using draw loop but optimized line draws
    for i in range(num_tracers):
        px = tx[i] * scale_x
        py = ty[i] * scale_y
        
        s = norm_speeds[i]
        r = int(s * 255 + (1 - s) * 20)
        g = int(s * 180 + (1 - s) * 200)
        b = int(s * 50 + (1 - s) * 255)
        
        py5.stroke(r, g, b, 150)
        vx_val = vx[i] * scale_x
        vy_val = vy[i] * scale_y
        py5.line(px, py, px - vx_val * 4.0, py - vy_val * 4.0)

    py5.no_fill()
    py5.stroke_weight(5.0)
    py5.stroke(255, 120, 0, 180)
    py5.circle(cx * scale_x, cy * scale_y, r_cylinder * 2 * scale_x)
    
    py5.fill(10, 10, 15, 240)
    py5.no_stroke()
    py5.circle(cx * scale_x, cy * scale_y, (r_cylinder - 0.5) * 2 * scale_x)

    py5.fill(255, 255, 255, 200)
    py5.text_size(24)
    py5.text("MODEL: FRISCH-HASSLACHER-POMEAU (FHP-I)", 60, 80)
    py5.text(f"GRID: {SIM_W}x{SIM_H} HEXAGONAL LATTICE", 60, 120)
    py5.text("REYNOLDS NUMBER: Re ~ 1200 (EST)", 60, 160)
    py5.text(f"TRACERS: {num_tracers} ACTIVE ACTIVE-MATTER PATHS", 60, 200)
    
    py5.text(f"FRAME: {py5.frame_count}/{TOTAL_FRAMES}", 60, h_screen - 80)
    py5.text("RENDER STATUS: 60FPS STABLE ENCODING", w_screen - 500, h_screen - 80)

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
