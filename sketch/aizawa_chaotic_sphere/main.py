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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
W, H = SIZE

NUM_PARTICLES = 1500000
dt = 0.015

# Aizawa Attractor parameters
A, B, C, D, E, F = 0.95, 0.7, 0.6, 3.5, 0.25, 0.1

particles = None
colors = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 10, 12)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, colors
    # Initialize particles near the origin
    particles = np.random.randn(NUM_PARTICLES, 3) * 0.1
    particles[:, 2] += 0.5 # Shift up slightly
    
    # Pre-generate colors based on particle ID
    hues = np.linspace(0, 360, NUM_PARTICLES)
    np.random.shuffle(hues)
    
    colors = np.zeros((NUM_PARTICLES, 3), dtype=np.uint8)
    # Simple color map
    # A mix of neon purple, pink, cyan
    for i in range(NUM_PARTICLES):
        h = hues[i]
        if h < 120: # Purple/Pink
            colors[i] = [255, 50, 150]
        elif h < 240: # Cyan
            colors[i] = [0, 200, 255]
        else: # Deep Blue
            colors[i] = [50, 100, 255]

def update_aizawa():
    global particles
    
    x = particles[:, 0]
    y = particles[:, 1]
    z = particles[:, 2]
    
    # Aizawa equations
    dx = (z - B) * x - D * y
    dy = D * x + (z - B) * y
    dz = C + A * z - (z**3) / 3.0 - (x**2 + y**2) * (1.0 + E * z) + F * z * (x**3)
    
    particles[:, 0] += dx * dt
    particles[:, 1] += dy * dt
    particles[:, 2] += dz * dt

def draw():
    # Motion blur trail
    py5.fill(10, 10, 12, 10)
    py5.no_stroke()
    py5.rect(0, 0, W, H)
    
    # Rotate the camera slowly over time
    t = py5.frame_count * 0.01
    
    # We will do multiple steps per frame to speed up the visual motion
    for _ in range(2):
        update_aizawa()
        
    x = particles[:, 0]
    y = particles[:, 1]
    z = particles[:, 2]
    
    # 3D Rotation matrices
    cos_t, sin_t = np.cos(t), np.sin(t)
    cos_t2, sin_t2 = np.cos(t * 0.5), np.sin(t * 0.5)
    
    # Rotate around Z axis
    x_rot = x * cos_t - y * sin_t
    y_rot = x * sin_t + y * cos_t
    
    # Rotate around X axis
    y_rot2 = y_rot * cos_t2 - z * sin_t2
    z_rot = y_rot * sin_t2 + z * cos_t2
    
    # Perspective projection
    fov = 500.0
    z_dist = 4.0
    
    z_factor = fov / (z_rot + z_dist)
    
    screen_x = x_rot * z_factor * 150.0 + W / 2
    screen_y = y_rot2 * z_factor * 150.0 + H / 2
    
    # Draw points directly to pixels
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Convert to int
    coords = np.column_stack((screen_x, screen_y)).astype(np.int32)
    
    # Filter valid coordinates
    valid = (coords[:, 0] >= 0) & (coords[:, 0] < W) & (coords[:, 1] >= 0) & (coords[:, 1] < H)
    
    v_coords = coords[valid]
    v_colors = colors[valid]
    v_z = z_rot[valid]
    
    # Dim particles further away
    dim_factor = np.clip(1.0 - (v_z + 1.0) / 4.0, 0.1, 1.0)
    
    r = (v_colors[:, 0] * dim_factor).astype(np.uint8)
    g = (v_colors[:, 1] * dim_factor).astype(np.uint8)
    b = (v_colors[:, 2] * dim_factor).astype(np.uint8)
    
    pixels[v_coords[:, 1], v_coords[:, 0], 1] = r
    pixels[v_coords[:, 1], v_coords[:, 0], 2] = g
    pixels[v_coords[:, 1], v_coords[:, 0], 3] = b
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
