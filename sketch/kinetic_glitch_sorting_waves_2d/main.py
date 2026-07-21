from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Number of vertical slices
NUM_SLICES = 600
SLICE_WIDTH = SIZE[0] / NUM_SLICES

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global offsets_y, lengths, hues
    offsets_y = np.random.uniform(0, 1000, NUM_SLICES)
    lengths = np.random.uniform(100, 800, NUM_SLICES)
    hues = np.random.uniform(0, 360, NUM_SLICES)
    
def draw():
    py5.background(15)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.no_stroke()
    
    # We will simulate a glitching landscape by drawing a grid of vertical rectangles
    for i in range(NUM_SLICES):
        x = i * SLICE_WIDTH
        
        # Base wave using Perlin noise
        noise_val = py5.noise(i * 0.05 + t * 5.0)
        
        # Glitch trigger
        glitch_chance = py5.noise(i * 0.1, t * 10.0)
        is_glitch = glitch_chance > 0.7
        
        # Base y position
        y = py5.height / 2 + (noise_val - 0.5) * py5.height * 0.8
        
        # Base height
        h = lengths[i] + math.sin(t * py5.TWO_PI + i * 0.1) * 200
        
        if is_glitch:
            y += (py5.noise(offsets_y[i] + t * 15.0) - 0.5) * py5.height * 0.5
            h *= 1.5 + py5.noise(i) * 2.0
            hue = (hues[i] + 180 + t * 360) % 360
            saturation = 100
            brightness = 100
        else:
            hue = (hues[i] + t * 180) % 360
            saturation = 60
            brightness = 70
            
        py5.fill(hue, saturation, brightness, 90)
        py5.rect(x, y - h / 2, SLICE_WIDTH, h)
        
        # Draw some horizontal glitch lines across
        if is_glitch and i % 5 == 0:
            py5.fill(0, 0, 100, 50)
            glitch_y = y + (py5.random(-1, 1) * h / 2)
            py5.rect(x - py5.random(50, 300), glitch_y, py5.random(100, 600), py5.random(2, 10))

    # Add a global scanline effect
    scan_y = (t * py5.height * 5) % py5.height
    py5.fill(0, 0, 100, 30)
    py5.rect(0, scan_y, py5.width, py5.height * 0.05)

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
        import os
        os._exit(0)

py5.run_sketch()
