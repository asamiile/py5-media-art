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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_hopper_crystal(depth, size, x, y, z, base_hue, step):
    if depth == 0 or size < 10:
        return
        
    py5.push_matrix()
    py5.translate(x, y, z)
    
    # Slight continuous rotation for the animation
    py5.rotate_z(py5.frame_count * 0.01 * (1 if depth % 2 == 0 else -1))
    
    # Iridescent coloring based on size and base hue
    hue = (base_hue + depth * 15 + py5.frame_count * 0.5) % 360
    py5.fill(hue, 70, 90)
    
    # Draw hollow-like box by drawing a frame or smaller boxes
    py5.box(size, size, size * 0.1)
    py5.pop_matrix()
    
    # Recursive calls for hopper effect (inward stepping)
    offset = size * 0.4
    new_size = size * 0.7
    new_z = z + size * 0.1
    
    # Only branch fully if step lets us, creating an animated growth effect
    current_growth = (py5.frame_count / TOTAL_FRAMES) * 15
    if depth < current_growth:
        draw_hopper_crystal(depth - 1, new_size, x + offset, y + offset, new_z, base_hue, step)
        draw_hopper_crystal(depth - 1, new_size, x - offset, y + offset, new_z, base_hue, step)
        draw_hopper_crystal(depth - 1, new_size, x + offset, y - offset, new_z, base_hue, step)
        draw_hopper_crystal(depth - 1, new_size, x - offset, y - offset, new_z, base_hue, step)

def draw():
    py5.background(10)
    py5.ambient_light(0, 0, 40)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(200, 50, 100, -1, -1, -0.5)
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    # Overall rotation
    py5.rotate_x(py5.PI / 3 + py5.sin(py5.frame_count * 0.01) * 0.2)
    py5.rotate_z(py5.frame_count * 0.005)
    
    py5.no_stroke()
    
    # Animate the recursion depth over time, ping-ponging
    growth_phase = py5.sin((py5.frame_count / TOTAL_FRAMES) * py5.PI)
    max_depth = int(3 + growth_phase * 4)
    
    draw_hopper_crystal(max_depth, 400, 0, 0, 0, 200, py5.frame_count)

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
