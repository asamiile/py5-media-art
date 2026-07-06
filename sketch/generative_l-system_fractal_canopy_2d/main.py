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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

MAX_DEPTH = 11

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(245, 240, 230)
    FRAMES_DIR.mkdir(exist_ok=True)

def branch(length, depth, wind_angle, growth_factor):
    # Base color: dark espresso brown (40, 25, 20)
    # Tip color: vibrant autumn (220, 60, 20) or (240, 160, 20)
    progress = 1.0 - (depth / MAX_DEPTH)
    
    # Interpolate color
    r = py5.lerp(40, 220, progress)
    g = py5.lerp(25, 60, progress)
    b = py5.lerp(20, 20, progress)
    
    if depth < 3:
        # Give tips some random yellowish variation based on position
        r = py5.lerp(r, 240, 0.5)
        g = py5.lerp(g, 160, 0.5)
        
    py5.stroke(r, g, b, 200)
    py5.stroke_weight(depth * 1.5 + 0.5)
    
    # The actual length takes growth_factor into account
    current_length = length * py5.constrain(growth_factor, 0, 1)
    
    py5.line(0, 0, 0, -current_length)
    py5.translate(0, -current_length)
    
    if depth > 0 and growth_factor > 0.1:
        # Branch angles
        angle_spread = py5.radians(25)
        
        # Wind effect increases towards the tips
        wind = wind_angle * (1.0 + progress * 2.0)
        
        py5.push_matrix()
        py5.rotate(wind + angle_spread)
        # Next branch growth is delayed slightly relative to parent
        branch(length * 0.72, depth - 1, wind_angle, (growth_factor - 0.05) * 1.2)
        py5.pop_matrix()
        
        py5.push_matrix()
        py5.rotate(wind - angle_spread)
        branch(length * 0.72, depth - 1, wind_angle, (growth_factor - 0.05) * 1.2)
        py5.pop_matrix()

def draw():
    py5.background(245, 240, 230)
    
    t = py5.frame_count * 0.005
    
    # Growth goes from 0 to 1 over the first half, then stays 1
    t_growth = py5.frame_count / (TOTAL_FRAMES * 0.4)
    
    # Wind using perlin noise
    wind = (py5.os_noise(t * 1.5, 0.0) - 0.5) * 0.15
    
    py5.translate(SIZE[0] / 2, SIZE[1])
    branch(SIZE[1] * 0.25, MAX_DEPTH, wind, t_growth)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
