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

NUM_PARTICLES = 15000
NOISE_SCALE = 0.003
EPS = 0.1

particles = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
colors = np.zeros((NUM_PARTICLES, 4), dtype=np.float32)

def curl_noise(x, y, z):
    # Calculate pseudo-curl noise using OpenSimplex
    n1 = py5.os_noise(x, y + EPS, z)
    n2 = py5.os_noise(x, y - EPS, z)
    n3 = py5.os_noise(x - EPS, y, z)
    n4 = py5.os_noise(x + EPS, y, z)
    
    # Curl formula: (dy, -dx) from scalar field
    cx = (n1 - n2) / (2 * EPS)
    cy = (n3 - n4) / (2 * EPS)
    return cx, cy

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 15)
    
    # Initialize particles randomly across the screen
    for i in range(NUM_PARTICLES):
        particles[i, 0] = py5.random(SIZE[0])
        particles[i, 1] = py5.random(SIZE[1])
        
        # Colors: mix of cyan, teal, magenta
        r = py5.random(1)
        if r < 0.33:
            colors[i] = [0, 255, 255, 150] # Cyan
        elif r < 0.66:
            colors[i] = [255, 0, 255, 100] # Magenta
        else:
            colors[i] = [0, 200, 150, 180] # Teal

def draw():
    # Draw semi-transparent background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 15, 10)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    z = py5.frame_count * 0.005
    
    # Batch drawing for performance
    py5.begin_shape(py5.POINTS)
    
    for i in range(NUM_PARTICLES):
        px, py = particles[i]
        
        cx, cy = curl_noise(px * NOISE_SCALE, py * NOISE_SCALE, z)
        
        # Velocity
        vx = cx * 8.0
        vy = cy * 8.0
        
        # Update position
        px += vx
        py += vy
        
        # Screen wrap
        if px < 0: px += SIZE[0]
        if px > SIZE[0]: px -= SIZE[0]
        if py < 0: py += SIZE[1]
        if py > SIZE[1]: py -= SIZE[1]
        
        particles[i, 0] = px
        particles[i, 1] = py
        
        c = colors[i]
        py5.stroke(c[0], c[1], c[2], c[3])
        py5.vertex(px, py)
        
    py5.end_shape()

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
