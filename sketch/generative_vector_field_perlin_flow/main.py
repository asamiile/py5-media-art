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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 30000

# We use NumPy to manage particles efficiently
px = np.random.uniform(0, SIZE[0], NUM_PARTICLES)
py = np.random.uniform(0, SIZE[1], NUM_PARTICLES)
vx = np.zeros(NUM_PARTICLES)
vy = np.zeros(NUM_PARTICLES)
colors = np.zeros(NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5)
    
def draw():
    global px, py, vx, vy, colors
    
    # Motion blur / fading trail effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 8) # Semi-transparent black
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.5)
    
    t = py5.frame_count * 0.005
    noise_scale = 0.002
    
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        # Calculate Perlin noise value for current position
        # We manually use py5.noise in a loop here. Since py5.noise isn't fully vectorized, 
        # it might be slightly slow for 30k, but usually manageable in pure P2D.
        angle = py5.noise(px[i] * noise_scale, py[i] * noise_scale, t) * py5.TWO_PI * 4
        
        # Update velocity based on vector field angle
        vx[i] = py5.cos(angle) * 2.0
        vy[i] = py5.sin(angle) * 2.0
        
        # Update position
        px[i] += vx[i]
        py[i] += vy[i]
        
        # Screen wrap
        if px[i] < 0: px[i] += py5.width
        if px[i] > py5.width: px[i] -= py5.width
        if py[i] < 0: py[i] += py5.height
        if py[i] > py5.height: py[i] -= py5.height
        
        # Determine color based on flow angle
        hue = (py5.degrees(angle) + t * 50) % 360
        py5.stroke(hue, 80, 80, 50)
        py5.vertex(px[i], py[i])
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
