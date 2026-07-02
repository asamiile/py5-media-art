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

W, H = SIZE
NUM_PARTICLES = 300000

# Particle arrays
px = np.random.uniform(0, W, NUM_PARTICLES).astype(np.float32)
py = np.random.uniform(0, H, NUM_PARTICLES).astype(np.float32)
age = np.random.uniform(0, 100, NUM_PARTICLES).astype(np.float32)

# Accumulation buffer for glowing trails
buffer = np.zeros((H, W), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global px, py, age, buffer
    
    t = py5.frame_count * 0.015
    
    # 1. Calculate analytical curl noise (divergence-free flow field)
    # Scalar potential: psi = A*sin(kx)*cos(ky) + ...
    # We use a sum of a few frequencies
    
    # Scale coordinates
    sx = px * 0.0015
    sy = py * 0.0015
    
    # Derivatives of the scalar potential to get velocity
    # psi(x,y) = sin(sx + t) * cos(sy - t) + 0.5 * sin(2*sx - t*0.5) * cos(2*sy + t*0.5)
    # Vx = d psi / dy
    # Vy = -d psi / dx
    
    vx = -np.sin(sx + t) * np.sin(sy - t) - np.sin(2*sx - t*0.5) * np.sin(2*sy + t*0.5)
    vy = -np.cos(sx + t) * np.cos(sy - t) - np.cos(2*sx - t*0.5) * np.cos(2*sy + t*0.5)
    
    # Add a slow drift
    vx += 0.2
    vy += 0.1
    
    # Normalize velocity slightly and apply speed
    speed = 3.5
    mag = np.sqrt(vx**2 + vy**2) + 1e-5
    vx = (vx / mag) * speed
    vy = (vy / mag) * speed
    
    # Update positions
    px += vx
    py += vy
    age += 1
    
    # Respawn out of bounds or old particles
    respawn = (px < 0) | (px >= W) | (py < 0) | (py >= H) | (age > 150)
    num_respawn = np.sum(respawn)
    if num_respawn > 0:
        px[respawn] = np.random.uniform(0, W, num_respawn).astype(np.float32)
        py[respawn] = np.random.uniform(0, H, num_respawn).astype(np.float32)
        age[respawn] = 0
        
    # Accumulate on buffer
    ix = np.clip(px.astype(np.int32), 0, W-1)
    iy = np.clip(py.astype(np.int32), 0, H-1)
    
    # Fast accumulation using bincount
    flat_idx = iy * W + ix
    counts = np.bincount(flat_idx, minlength=W*H)
    buffer += counts.reshape((H, W)) * 0.15
    
    # Fade the buffer (motion blur / trail effect)
    buffer *= 0.92
    
    # Map buffer to colors (Bioluminescent teal / magenta / lime)
    # Background: Navy #050510 (R=5, G=5, B=16)
    
    intensity = np.clip(buffer, 0, 1.5)
    
    # Color mapping:
    # low intensity -> navy
    # mid intensity -> teal
    # high intensity -> bright lime / magenta
    
    R = 5.0 + intensity * 10.0 + (intensity > 0.8) * (intensity - 0.8) * 200.0
    G = 5.0 + intensity * 180.0 + (intensity > 1.2) * (intensity - 1.2) * 100.0
    B = 16.0 + intensity * 200.0 - (intensity > 0.6) * (intensity - 0.6) * 100.0
    
    R = np.clip(R, 0, 255).astype(np.uint8)
    G = np.clip(G, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)
    
    alpha = np.full((H, W, 1), 255, dtype=np.uint8)
    rgb = np.stack((R, G, B), axis=-1)
    argb = np.concatenate((alpha, rgb), axis=-1)
    
    py5.load_np_pixels()
    py5.np_pixels[:] = argb
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
