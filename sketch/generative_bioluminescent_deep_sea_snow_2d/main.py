from pathlib import Path
import shutil
import subprocess
import sys
import random
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

num_particles = 3000
particles = None

def setup():
    # Use default 2D renderer to avoid any P3D crash on macOS
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global particles
    particles = np.zeros((num_particles, 6), dtype=np.float32)
    particles[:, 0] = np.random.uniform(0, SIZE[0], num_particles)
    particles[:, 1] = np.random.uniform(-SIZE[1], SIZE[1]*2, num_particles)
    particles[:, 2] = np.random.uniform(0.1, 2.0, num_particles) # Z-depth scale
    particles[:, 3] = np.random.uniform(4, 20, num_particles) # Size
    particles[:, 4] = np.random.uniform(160, 220, num_particles) # Hue
    particles[:, 5] = np.random.uniform(0, py5.TWO_PI, num_particles) # Phase
    
    py5.background(220, 80, 5) # initial bg

def draw():
    # Draw background with low alpha to leave trails
    py5.blend_mode(py5.BLEND)
    py5.fill(220, 80, 5, 20)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.01
    
    # Draw glowing central organic structure
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    py5.rotate(time_val * -0.5)
    for i in range(12):
        py5.rotate(py5.TWO_PI / 12)
        py5.push_matrix()
        py5.translate(200 + np.sin(time_val)*50, 0)
        py5.no_fill()
        hue = 180 + 40 * np.sin(time_val * 5 + i)
        py5.stroke(hue, 90, 80, 50)
        py5.stroke_weight(4)
        py5.begin_shape()
        for j in range(25):
            r = j * 20
            theta = np.sin(time_val * 3 + j * 0.3) * 1.5
            x_offset = r * np.cos(theta)
            y_offset = r * np.sin(theta)
            py5.curve_vertex(x_offset, y_offset)
        py5.end_shape()
        py5.pop_matrix()
    py5.pop_matrix()
    
    # Update and draw particles simulating parallax
    for i in range(num_particles):
        z = particles[i, 2]
        particles[i, 1] -= 2.0 * z # Fall speed proportional to depth
        particles[i, 0] += np.sin(time_val + particles[i, 5]) * 0.5 * z
        
        x, y = particles[i, 0], particles[i, 1]
        s, h, p = particles[i, 3], particles[i, 4], particles[i, 5]
        
        py5.no_stroke()
        alpha = 10 + 60 * np.sin(p + time_val * 2)
        if alpha > 0:
            py5.fill(h, 80, 100, alpha * min(z, 1.0)) # don't overdrive alpha too much
            py5.ellipse(x, y, s * z, s * z)
        
        if particles[i, 1] < -100:
            particles[i, 1] += SIZE[1] + 200
            particles[i, 0] = np.random.uniform(0, SIZE[0])

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
