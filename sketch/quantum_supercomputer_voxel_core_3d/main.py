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
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0) # Pitch black
    py5.lights()
    
    # Point light inside the core
    py5.point_light(200, 100, 100, SIZE[0]/2, SIZE[1]/2, 0)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, -600)
    
    t_phase = (py5.frame_count / TOTAL_FRAMES) * py5.TWO_PI
    
    # Slowly rotate the entire supercomputer core
    py5.rotate_x(t_phase)
    py5.rotate_y(t_phase * 0.5)
    
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    
    grid_size = 18
    spacing = 60
    offset = (grid_size * spacing) / 2
    
    for x in range(grid_size):
        for y in range(grid_size):
            for z in range(grid_size):
                # Complex trigonometric interference pattern ensuring a perfect 10s loop
                n = (np.sin(x * 0.35 + t_phase) + 
                     np.cos(y * 0.35 - t_phase * 2) + 
                     np.sin(z * 0.35 + t_phase)) / 3.0
                
                box_size = py5.remap(n, -1, 1, 0, spacing * 1.5)
                
                # Only draw boxes above a certain size threshold to create a porous structure
                if box_size > spacing * 0.3:
                    with py5.push_matrix():
                        py5.translate(x * spacing - offset, y * spacing - offset, z * spacing - offset)
                        
                        # Color shifts between deep royal blue and electric cyan based on interference
                        hue = (200 + n * 40) % 360
                        brightness = py5.remap(n, -1, 1, 30, 100)
                        
                        py5.fill(hue, 90, brightness, 70)
                        py5.box(box_size)

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
