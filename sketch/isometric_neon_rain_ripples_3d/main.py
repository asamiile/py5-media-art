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

raindrops = []
ripples = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    global raindrops, ripples
    py5.background(10, 80, 10)
    
    # Setup Isometric camera
    py5.ortho(-SIZE[0]/1.5, SIZE[0]/1.5, -SIZE[1]/1.5, SIZE[1]/1.5, -5000, 5000)
    py5.camera(1000, 1000, 1000, 0, 0, 0, 0, 1, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    # Spawn new raindrops
    if py5.frame_count % 3 == 0:
        x = py5.random(-800, 800)
        z = py5.random(-800, 800)
        color_val = random.choice([180, 300]) # Cyan or Magenta
        raindrops.append({'x': x, 'y': -1500, 'z': z, 'vy': 40, 'color': color_val})
        
    # Draw drops and check collisions
    active_drops = []
    py5.stroke_weight(4)
    for d in raindrops:
        d['vy'] += 1.5 # Gravity
        d['y'] += d['vy']
        
        # Draw drop line
        py5.stroke(d['color'], 80, 100, 80)
        py5.line(d['x'], d['y'], d['z'], d['x'], d['y'] - d['vy']*2, d['z'])
        
        if d['y'] > 0:
            # Hit the ground
            ripples.append({'x': d['x'], 'z': d['z'], 'r': 0, 'life': 200, 'color': d['color']})
        else:
            active_drops.append(d)
    raindrops = active_drops
    
    # Draw ripples
    active_ripples = []
    py5.stroke_weight(6)
    
    py5.push_matrix()
    py5.rotate_x(py5.PI/2)
    
    # Draw floor grid
    py5.stroke(200, 40, 20, 30)
    py5.stroke_weight(2)
    grid_size = 100
    for i in range(-10, 11):
        py5.line(i*grid_size, -1000, i*grid_size, 1000)
        py5.line(-1000, i*grid_size, 1000, i*grid_size)
    
    py5.stroke_weight(8)
    for r in ripples:
        r['r'] += 8 # Expansion speed
        r['life'] -= 2
        
        alpha = py5.remap(r['life'], 0, 200, 0, 100)
        py5.stroke(r['color'], 80, 100, alpha)
        
        py5.push_matrix()
        py5.translate(r['x'], r['z'], 0)
        py5.ellipse(0, 0, r['r']*2, r['r']*2)
        py5.pop_matrix()
        
        if r['life'] > 0:
            active_ripples.append(r)
            
    py5.pop_matrix()
    
    ripples = active_ripples
    
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
