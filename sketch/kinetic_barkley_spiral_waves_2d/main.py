from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.ndimage import map_coordinates

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

# Grid Size
W, H = SIZE
SCALE = 2 # Simulate RD on half resolution to save time, advect particles on full
W_sim = W // SCALE
H_sim = H // SCALE

NUM_PARTICLES = 1500000
STEPS_PER_FRAME = 8
DT = 0.01

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global u, v, p_pos, colormap
    
    # Initialize Barkley Model fields (u = excited, v = refractory)
    u = np.zeros((H_sim, W_sim), dtype=np.float32)
    v = np.zeros((H_sim, W_sim), dtype=np.float32)
    
    # Kickstart with random noise squares to spawn many spirals
    for _ in range(50):
        x = np.random.randint(0, W_sim - 20)
        y = np.random.randint(0, H_sim - 20)
        u[y:y+20, x:x+20] = np.random.rand()
        v[y:y+20, x:x+20] = np.random.rand()
        
    # Init particles
    p_pos = np.random.uniform(0, 1, (NUM_PARTICLES, 2)).astype(np.float32)
    p_pos[:, 0] *= W
    p_pos[:, 1] *= H
    
    # Bioluminescent Colormap (Deep Blue -> Cyan -> Emerald Green)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        val = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if val < 0.33:
            p = val / 0.33
            colormap[i, 1:] = [0, int(p * 50), 50 + int(p * 150)] # Dark to Deep Blue
        elif val < 0.66:
            p = (val - 0.33) / 0.33
            colormap[i, 1:] = [0, 50 + int(p * 150), 200 + int(p * 55)] # Deep Blue to Cyan
        else:
            p = (val - 0.66) / 0.34
            colormap[i, 1:] = [int(p * 100), 200 + int(p * 55), 255 - int(p * 155)] # Cyan to Green/White

def step_physics():
    global u, v, p_pos
    
    # Barkley Model Parameters
    a = 0.75
    b = 0.02
    eps = 0.02
    D = 1.0
    
    # Laplacian using finite differences
    lap_u = (np.roll(u, 1, axis=0) + np.roll(u, -1, axis=0) + 
             np.roll(u, 1, axis=1) + np.roll(u, -1, axis=1) - 4.0 * u)
             
    thresh = (v + b) / a
    du = (1.0 / eps) * u * (1.0 - u) * (u - thresh) + D * lap_u
    dv = u - v
    
    u += du * DT
    v += dv * DT
    
    # Clip to avoid explosion
    u = np.clip(u, -0.1, 1.1)
    v = np.clip(v, -0.1, 1.1)
    
    # Calculate gradients of U to drive the particles
    # We want particles to flow ALONG the wavefronts, so we take the perpendicular to the gradient
    grad_u_y = 0.5 * (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0))
    grad_u_x = 0.5 * (np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1))
    
    # Velocity field (perpendicular to gradient + small inward pull)
    vel_x = -grad_u_y + grad_u_x * 0.2
    vel_y = grad_u_x + grad_u_y * 0.2
    
    # Interpolate velocity at particle positions
    p_y_sim = p_pos[:, 1] / SCALE
    p_x_sim = p_pos[:, 0] / SCALE
    
    p_vx = map_coordinates(vel_x, [p_y_sim, p_x_sim], mode='wrap', order=1)
    p_vy = map_coordinates(vel_y, [p_y_sim, p_x_sim], mode='wrap', order=1)
    
    # Move particles
    # Scale velocity up because gradients are small
    speed_mult = 1500.0
    p_pos[:, 0] = (p_pos[:, 0] + p_vx * speed_mult * DT) % W
    p_pos[:, 1] = (p_pos[:, 1] + p_vy * speed_mult * DT) % H

def draw():
    global u, v, p_pos
    
    for _ in range(STEPS_PER_FRAME):
        step_physics()
        
    py5.load_np_pixels()
    
    # Deep space fade (motion blur)
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 235 // 256).astype(np.uint8)
    
    # Color particles based on the local 'u' value (excitation)
    p_y_sim = p_pos[:, 1] / SCALE
    p_x_sim = p_pos[:, 0] / SCALE
    p_u = map_coordinates(u, [p_y_sim, p_x_sim], mode='wrap', order=1)
    
    # Enhance contrast
    normalized_u = np.clip(p_u * 1.5, 0.0, 1.0)
    color_indices = (normalized_u * 255).astype(np.uint8)
    
    sx = p_pos[:, 0].astype(np.int32)
    sy = p_pos[:, 1].astype(np.int32)
    
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
