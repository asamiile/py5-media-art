from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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

# SDF Flow Parameters
NUM_PARTICLES = 600000
STEPS_PER_FRAME = 2
DT = 1.0

def map_sdf(px, py, t):
    x = np.copy(px)
    y = np.copy(py)
    
    # Center origin
    x -= SIZE[0] / 2
    y -= SIZE[1] / 2
    
    # Global rotation
    theta = t * 0.3
    c, s = np.cos(theta), np.sin(theta)
    nx = x * c - y * s
    ny = x * s + y * c
    x, y = nx, ny
    
    # Kaleidoscopic iterated folding
    for i in range(5):
        # Fold
        x = np.abs(x)
        y = np.abs(y)
        
        # Shift
        offset = 200.0 / (i + 1.0)
        x -= offset
        y -= offset
        
        # Rotate
        a = 0.6 + t * 0.15 * (1 if i % 2 == 0 else -1)
        ca, sa = np.cos(a), np.sin(a)
        nx = x * ca - y * sa
        ny = x * sa + y * ca
        x, y = nx, ny
        
    # Final SDF: A circle
    d = np.sqrt(x*x + y*y) - 30.0
    
    # Add fluid organic distortion
    d += 15.0 * np.sin(px * 0.01 + t * 2.0) * np.cos(py * 0.012 - t * 1.5)
    return d

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colormap
    
    W, H = SIZE
    pos = np.random.uniform(0, max(W, H), (NUM_PARTICLES, 2)).astype(np.float32)
    pos[:, 0] = pos[:, 0] % W
    pos[:, 1] = pos[:, 1] % H
    
    vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    
    # Pre-generate an electric neon colormap (Deep Blue -> Magenta -> Orange -> Yellow -> White)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.25:
            p = v / 0.25
            colormap[i, 1:] = [int(p * 150), 0, int(p * 200)] # Blue to Magenta
        elif v < 0.5:
            p = (v - 0.25) / 0.25
            colormap[i, 1:] = [150 + int(p * 105), int(p * 100), 200 - int(p * 200)] # Magenta to Orange
        elif v < 0.75:
            p = (v - 0.5) / 0.25
            colormap[i, 1:] = [255, 100 + int(p * 100), 0] # Orange to Yellow
        else:
            p = (v - 0.75) / 0.25
            colormap[i, 1:] = [255, 200 + int(p * 55), int(p * 255)] # Yellow to White

def step_physics(t):
    global pos, vel
    
    px = pos[:, 0]
    py = pos[:, 1]
    
    # Numerical gradient of SDF
    eps = 0.5
    d = map_sdf(px, py, t)
    dx = map_sdf(px + eps, py, t) - map_sdf(px - eps, py, t)
    dy = map_sdf(px, py + eps, t) - map_sdf(px, py - eps, t)
    
    # Normalize gradient
    grad_mag = np.sqrt(dx*dx + dy*dy) + 0.0001
    nx = dx / grad_mag
    ny = dy / grad_mag
    
    # 1. Flow along the contours (perpendicular to gradient)
    vx = ny
    vy = -nx
    
    # 2. Attraction to the surface (SDF = 0)
    # If d > 0, move against gradient. If d < 0, move with gradient.
    vx -= nx * d * 0.05
    vy -= ny * d * 0.05
    
    # Speed modulation
    speed = 4.0
    vel[:, 0] = vx * speed
    vel[:, 1] = vy * speed
    
    pos += vel * DT
    
    # Add thermal noise
    pos += np.random.uniform(-0.5, 0.5, (NUM_PARTICLES, 2))
    
    # Toroidal wrap
    W, H = SIZE
    pos[:, 0] = pos[:, 0] % W
    pos[:, 1] = pos[:, 1] % H

def draw():
    global pos, vel
    
    t = py5.frame_count * 0.015
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Deep fade for fluid motion blur
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 220 // 256).astype(np.uint8)
    
    sx = pos[:, 0].astype(np.int32)
    sy = pos[:, 1].astype(np.int32)
    
    W, H = SIZE
    valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx = sx[valid]
    sy = sy[valid]
    
    # Color based on kinetic energy
    v_mag = np.sqrt(vel[valid, 0]**2 + vel[valid, 1]**2)
    intensity = np.clip(v_mag * 40.0, 0, 255).astype(np.uint8)
    
    vr = colormap[intensity, 1]
    vg = colormap[intensity, 2]
    vb = colormap[intensity, 3]
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    flat_pixels[flat_indices, 1] = np.clip(flat_pixels[flat_indices, 1].astype(np.uint16) + vr, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 2] = np.clip(flat_pixels[flat_indices, 2].astype(np.uint16) + vg, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 3] = np.clip(flat_pixels[flat_indices, 3].astype(np.uint16) + vb, 0, 255).astype(np.uint8)
    
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
