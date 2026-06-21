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

num_particles = 15000
particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(220, 90, 10) # very dark blue
    py5.no_stroke()
    
    # Initialize particles
    for _ in range(num_particles):
        particles.append([
            py5.random(py5.width),
            py5.random(py5.height),
            py5.random(180, 220) # hues (blue/cyan)
        ])

def draw():
    # Very faint fade for long silky trails
    py5.fill(220, 90, 10, 5)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    noise_scale = 0.002
    
    for p in particles:
        x, y, hue = p
        
        # Flow field angle
        angle = py5.os_noise(x * noise_scale, y * noise_scale, t) * py5.TWO_PI * 4
        
        # Velocity
        vx = py5.cos(angle) * 3
        vy = py5.sin(angle) * 3
        
        nx = x + vx
        ny = y + vy
        
        # Draw line segment
        py5.stroke(hue, 80, 100, 30)
        py5.stroke_weight(1.5)
        py5.line(x, y, nx, ny)
        
        # Update pos
        p[0] = nx
        p[1] = ny
        
        # Wrap around
        if nx < 0: p[0] += py5.width
        if nx > py5.width: p[0] -= py5.width
        if ny < 0: p[1] += py5.height
        if ny > py5.height: p[1] -= py5.height

    py5.blend_mode(py5.BLEND)
    py5.no_stroke()

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
