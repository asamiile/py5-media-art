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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 10000
particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10)
    
    # Initialize particles randomly across the plate
    for _ in range(num_particles):
        particles.append([
            py5.random(-py5.width/2, py5.width/2),
            py5.random(-py5.height/2, py5.height/2),
            0.0, # vx
            0.0  # vy
        ])
        
    py5.no_stroke()

def draw():
    py5.background(10, 10, 15, 60)
    
    py5.translate(py5.width/2, py5.height/2, -500)
    
    # Rotate plate slowly
    py5.rotate_x(py5.PI / 4)
    py5.rotate_z(py5.frame_count * 0.005)
    
    # Parameters for Chladni patterns
    # Chladni equation: cos(n*x)*cos(m*y) - cos(m*x)*cos(n*y) = 0
    t = py5.frame_count * 0.02
    n = 2 + py5.sin(t*0.5) * 1.5
    m = 5 + py5.cos(t*0.3) * 2.0
    
    scale = 0.005
    
    # Draw plate
    py5.fill(20, 20, 30)
    py5.rect(-py5.width/2, -py5.height/2, py5.width, py5.height)
    
    # Draw particles
    py5.fill(255, 215, 0, 200) # Gold
    
    for p in particles:
        x, y, vx, vy = p
        
        # Calculate gradient of the Chladni field to find nodes (where value is 0)
        # Value = cos(n*pi*x/L)*cos(m*pi*y/L) - cos(m*pi*x/L)*cos(n*pi*y/L)
        val = py5.cos(n * x * scale) * py5.cos(m * y * scale) - py5.cos(m * x * scale) * py5.cos(n * y * scale)
        
        # Force pushes particles away from anti-nodes (high vibration) towards nodes (zero vibration)
        # We approximate this by pushing them down the absolute value gradient
        # Perturb with noise to simulate bouncing
        noise_ang = py5.os_noise(x * 0.01, y * 0.01, t) * py5.TWO_PI * 2
        bounce_mag = abs(val) * 5.0
        
        p[2] = (vx + py5.cos(noise_ang) * bounce_mag) * 0.8
        p[3] = (vy + py5.sin(noise_ang) * bounce_mag) * 0.8
        
        p[0] += p[2]
        p[1] += p[3]
        
        # Constrain to plate
        if p[0] < -py5.width/2: p[0] = py5.width/2
        if p[0] > py5.width/2: p[0] = -py5.width/2
        if p[1] < -py5.height/2: p[1] = py5.height/2
        if p[1] > py5.height/2: p[1] = -py5.height/2
        
        # Render particle bouncing up and down based on vibration (val)
        z = abs(val) * 50.0
        
        py5.push_matrix()
        py5.translate(p[0], p[1], z)
        py5.sphere(3)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
