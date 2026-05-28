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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global buildings
    buildings = []
    py5.random_seed(42)
    
    # Generate random buildings
    for _ in range(150):
        x = py5.random(-1500, 1500)
        z = py5.random(-2000, 500)
        
        # Don't place buildings in the "road" in the middle
        if -300 < x < 300:
            continue
            
        w = py5.random(80, 250)
        d = py5.random(80, 250)
        h = py5.random(200, 1200)
        buildings.append((x, z, w, d, h))

def draw():
    py5.background(270, 80, 10)
    
    t = py5.frame_count * 15.0  # Speed of movement
    
    py5.push_matrix()
    
    # Set camera
    py5.camera(0, -300, 1200, 0, -200, 0, 0, 1, 0)
    
    # Draw Glowing Sun
    py5.push_matrix()
    py5.translate(0, -600, -2500)
    py5.no_stroke()
    for i in range(10):
        py5.fill(330, 90, 100, 10)
        py5.circle(0, 0, 1000 + i * 20)
    py5.pop_matrix()
    
    # Draw Grid Floor
    py5.stroke_weight(4)
    py5.stroke(300, 90, 100, 60)
    
    grid_size = 200
    z_offset = t % grid_size
    
    # Vertical lines
    for x in range(-2000, 2001, grid_size):
        py5.line(x, 0, -3000, x, 0, 1000)
        
    # Horizontal lines
    for z in range(-3000, 1001, grid_size):
        z_pos = z + z_offset
        if z_pos > 1000:
            continue
        py5.line(-2000, 0, z_pos, 2000, 0, z_pos)
        
    # Draw Buildings
    py5.stroke(180, 90, 100, 80)
    py5.stroke_weight(2)
    
    for (bx, bz, bw, bd, bh) in buildings:
        # Move buildings towards camera
        current_z = bz + t
        
        # Wrap buildings around when they pass the camera
        if current_z > 1200:
            current_z -= 3500
            
        py5.push_matrix()
        py5.translate(bx, -bh/2, current_z)
        py5.fill(280, 90, 10, 80) # Dark purple sides
        py5.box(bw, bh, bd)
        py5.pop_matrix()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
