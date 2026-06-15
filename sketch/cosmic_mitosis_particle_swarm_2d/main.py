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

NUM_PARTICLES = 3000
particles = None

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # [x, y, vx, vy, hue]
    particles = np.zeros((NUM_PARTICLES, 5))
    
    # Initialize in a center blob
    angles = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    radii = np.random.normal(100, 50, NUM_PARTICLES)
    particles[:, 0] = py5.width / 2 + np.cos(angles) * radii
    particles[:, 1] = py5.height / 2 + np.sin(angles) * radii
    particles[:, 4] = np.random.uniform(280, 320, NUM_PARTICLES) # Purple/Pink hues

def draw():
    global particles
    
    # Semi-transparent background for trails
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Centers splitting apart
    center1_x = py5.width / 2 - 300 * t
    center1_y = py5.height / 2 + 100 * py5.sin(t * py5.TWO_PI)
    
    center2_x = py5.width / 2 + 300 * t
    center2_y = py5.height / 2 - 100 * py5.sin(t * py5.TWO_PI)
    
    # Numpy calculations
    px = particles[:, 0]
    py = particles[:, 1]
    
    dx1 = center1_x - px
    dy1 = center1_y - py
    dist1 = np.sqrt(dx1**2 + dy1**2) + 0.1
    
    dx2 = center2_x - px
    dy2 = center2_y - py
    dist2 = np.sqrt(dx2**2 + dy2**2) + 0.1
    
    # Split population
    mask = (particles[:, 4] < 300)
    
    # Attraction towards centers
    particles[mask, 2] += dx1[mask] / dist1[mask] * 2.0
    particles[mask, 3] += dy1[mask] / dist1[mask] * 2.0
    
    particles[~mask, 2] += dx2[~mask] / dist2[~mask] * 2.0
    particles[~mask, 3] += dy2[~mask] / dist2[~mask] * 2.0
    
    # Flow field noise
    noise_x = np.array([py5.os_noise(x * 0.005, y * 0.005, t * 5) for x, y in zip(px, py)])
    noise_y = np.array([py5.os_noise(x * 0.005 + 1000, y * 0.005 + 1000, t * 5) for x, y in zip(px, py)])
    
    particles[:, 2] += (noise_x - 0.5) * 5.0
    particles[:, 3] += (noise_y - 0.5) * 5.0
    
    # Friction
    particles[:, 2] *= 0.9
    particles[:, 3] *= 0.9
    
    particles[:, 0] += particles[:, 2]
    particles[:, 1] += particles[:, 3]
    
    # Rendering
    py5.stroke_weight(3)
    for p in particles:
        speed = np.sqrt(p[2]**2 + p[3]**2)
        hue = (p[4] + speed * 2) % 360
        py5.stroke(hue, 90, 100, 60)
        py5.point(p[0], p[1])
        
    py5.blend_mode(py5.BLEND)

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
