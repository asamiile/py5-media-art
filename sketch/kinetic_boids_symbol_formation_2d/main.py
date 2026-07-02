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

NUM_PARTICLES = 4000
particles = None
targets = None

def setup():
    global particles, targets
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # [x, y, vx, vy, hue]
    particles = np.zeros((NUM_PARTICLES, 5))
    
    # Initialize in a random explosion pattern
    angles = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    radii = np.random.uniform(0, py5.width, NUM_PARTICLES)
    particles[:, 0] = py5.width / 2 + np.cos(angles) * radii
    particles[:, 1] = py5.height / 2 + np.sin(angles) * radii
    particles[:, 2] = np.cos(angles) * np.random.uniform(1, 5, NUM_PARTICLES)
    particles[:, 3] = np.sin(angles) * np.random.uniform(1, 5, NUM_PARTICLES)
    particles[:, 4] = np.random.uniform(150, 250, NUM_PARTICLES) # Cyan/Blue hues
    
    # Generate target points (a complex Lissajous knot)
    targets = np.zeros((NUM_PARTICLES, 2))
    for i in range(NUM_PARTICLES):
        t = i / float(NUM_PARTICLES) * np.pi * 20
        # A 5:4 Lissajous knot
        targets[i, 0] = py5.width / 2 + 500 * np.sin(5 * t + np.pi/4)
        targets[i, 1] = py5.height / 2 + 400 * np.sin(4 * t)

def draw():
    global particles, targets
    
    # Fading trails
    py5.fill(0, 0, 0, 25)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Animation phase: 
    # 0.0 - 0.2: Chaos
    # 0.2 - 0.7: Form target symbol
    # 0.7 - 1.0: Explode
    
    form_strength = 0.0
    if 0.2 < t < 0.7:
        # Ramp up
        if t < 0.3:
            form_strength = (t - 0.2) / 0.1
        elif t > 0.6:
            form_strength = (0.7 - t) / 0.1
        else:
            form_strength = 1.0
            
    # Force towards targets
    px = particles[:, 0]
    py = particles[:, 1]
    
    tx = targets[:, 0]
    ty = targets[:, 1]
    
    dx = tx - px
    dy = ty - py
    
    dist = np.sqrt(dx**2 + dy**2) + 0.1
    
    # Target attraction
    particles[:, 2] += (dx / dist) * form_strength * 2.0
    particles[:, 3] += (dy / dist) * form_strength * 2.0
    
    # Noise/Wander force (stronger when form_strength is low)
    chaos_strength = 1.0 - form_strength * 0.8
    noise_angles = np.array([py5.os_noise(x * 0.005, y * 0.005, t * 5) * py5.TWO_PI * 4 for x, y in zip(px, py)])
    particles[:, 2] += np.cos(noise_angles) * chaos_strength
    particles[:, 3] += np.sin(noise_angles) * chaos_strength
    
    # Explosion trigger at t=0.7
    if py5.frame_count == int(TOTAL_FRAMES * 0.7):
        exp_angles = np.random.uniform(0, py5.TWO_PI, NUM_PARTICLES)
        particles[:, 2] += np.cos(exp_angles) * 30.0
        particles[:, 3] += np.sin(exp_angles) * 30.0
    
    # Friction
    particles[:, 2] *= 0.92
    particles[:, 3] *= 0.92
    
    particles[:, 0] += particles[:, 2]
    particles[:, 1] += particles[:, 3]
    
    # Screen wrap
    particles[:, 0] = particles[:, 0] % py5.width
    particles[:, 1] = particles[:, 1] % py5.height
    
    # Rendering
    py5.stroke_weight(2)
    for p in particles:
        speed = np.sqrt(p[2]**2 + p[3]**2)
        hue = (p[4] + speed * 10) % 360
        py5.stroke(hue, 90, 100, 80)
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
