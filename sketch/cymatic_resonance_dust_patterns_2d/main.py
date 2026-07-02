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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 30000
particles = None

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # [x, y, vx, vy]
    particles = np.zeros((NUM_PARTICLES, 4))
    
    # Initialize randomly across canvas
    particles[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)

def get_chladni_field(x, y, t):
    # Normalized coordinates
    nx = x / py5.width * 2.0 - 1.0
    ny = y / py5.height * 2.0 - 1.0
    
    # Evolving frequencies
    n = 5.0 + np.sin(t * np.pi) * 2.0
    m = 4.0 + np.cos(t * np.pi) * 2.0
    
    # Chladni equation
    val = np.cos(n * np.pi * nx) * np.cos(m * np.pi * ny) - np.cos(m * np.pi * nx) * np.cos(n * np.pi * ny)
    return val

def draw():
    global particles
    
    # Very slight fade for ghosting trails
    py5.fill(0, 0, 0, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    px = particles[:, 0]
    py = particles[:, 1]
    
    # Approximate gradient of Chladni field using finite differences
    eps = 2.0
    
    # Compute field values at p
    val_center = get_chladni_field(px, py, t)
    
    val_dx = get_chladni_field(px + eps, py, t)
    val_dy = get_chladni_field(px, py + eps, t)
    
    # Gradient pushes particles towards nodes (where val == 0)
    # We want particles to roll down the absolute value of the field
    # grad(|F|) = F/|F| * grad(F)
    
    grad_x = (val_dx - val_center) / eps
    grad_y = (val_dy - val_center) / eps
    
    sign_F = np.sign(val_center)
    # Avoid zero division or nan
    sign_F[sign_F == 0] = 1.0
    
    force_x = -sign_F * grad_x
    force_y = -sign_F * grad_y
    
    # Add some vibration/noise
    noise_x = np.random.normal(0, 1.0, NUM_PARTICLES)
    noise_y = np.random.normal(0, 1.0, NUM_PARTICLES)
    
    # Apply forces
    force_mult = 20.0
    particles[:, 2] += force_x * force_mult + noise_x
    particles[:, 3] += force_y * force_mult + noise_y
    
    # Friction
    particles[:, 2] *= 0.85
    particles[:, 3] *= 0.85
    
    particles[:, 0] += particles[:, 2]
    particles[:, 1] += particles[:, 3]
    
    # Keep on screen
    particles[:, 0] = particles[:, 0] % py5.width
    particles[:, 1] = particles[:, 1] % py5.height
    
    # Rendering particles
    py5.stroke_weight(2)
    for p in particles:
        speed = np.sqrt(p[2]**2 + p[3]**2)
        hue = (220 + speed * 15) % 360
        py5.stroke(hue, 70, 100, 30)
        py5.point(p[0], p[1])
        
    py5.blend_mode(py5.BLEND)

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
        
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.5):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
