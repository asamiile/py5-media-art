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

# Particle parameters - reduced for speed
NUM_PARTICLES = 30000
particles = None

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles: x, y, hue
    particles = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    particles[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    
    # Base hues (violet, cyan, pink)
    base_hues = [275, 180, 320]
    choices = np.random.choice(base_hues, NUM_PARTICLES)
    particles[:, 2] = choices + np.random.uniform(-10, 10, NUM_PARTICLES)

def draw():
    global particles
    
    # Motion blur / fade
    py5.fill(0, 0, 0, 25)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.01
    
    # Calculate vector field
    x = particles[:, 0]
    y = particles[:, 1]
    
    # Two moving dipole centers
    cx1 = py5.width/2 + np.cos(t) * py5.width * 0.25
    cy1 = py5.height/2 + np.sin(t * 1.3) * py5.height * 0.25
    
    cx2 = py5.width/2 + np.sin(t * 0.8) * py5.width * 0.3
    cy2 = py5.height/2 + np.cos(t * 1.1) * py5.height * 0.3
    
    dx1, dy1 = x - cx1, y - cy1
    dx2, dy2 = x - cx2, y - cy2
    
    d1 = np.sqrt(dx1**2 + dy1**2) + 1.0
    d2 = np.sqrt(dx2**2 + dy2**2) + 1.0
    
    # Vortex/curl components
    vx = -dy1 / d1 * 5.0 + dy2 / d2 * 4.0
    vy = dx1 / d1 * 5.0 - dx2 / d2 * 4.0
    
    # Add curl noise using simple trig functions for speed
    nx = np.sin(y * 0.005 + t) * 2.0
    ny = np.cos(x * 0.005 + t) * 2.0
    
    particles[:, 0] += vx + nx
    particles[:, 1] += vy + ny
    
    # Wrap edges
    particles[:, 0] = np.mod(particles[:, 0], py5.width)
    particles[:, 1] = np.mod(particles[:, 1], py5.height)
    
    # Draw points directly for speed
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2) # make points a bit larger since there are fewer
    
    # Batch by hue
    for hue_center in [275, 180, 320]:
        mask = (particles[:, 2] >= hue_center - 15) & (particles[:, 2] <= hue_center + 15)
        batch = particles[mask]
        if len(batch) > 0:
            py5.stroke(hue_center, 80, 100, 40)
            coords = batch[:, :2]
            py5.points(coords)
            
    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.", flush=True)
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.", flush=True)
            
        import os
        os._exit(0)

py5.run_sketch()
