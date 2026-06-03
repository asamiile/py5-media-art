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

COLS, ROWS = 16, 16
CELL_SIZE = 120
W = COLS * CELL_SIZE
H = ROWS * CELL_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(220, 220, 225) # Pale Concrete Grey
    
    # Harsh architectural lighting
    py5.ambient_light(50, 50, 55)
    py5.directional_light(255, 250, 240, 0.8, 0.5, -1) # Warm sun from top right
    py5.directional_light(80, 100, 150, -1, -0.5, 0.5) # Cool fill light
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    t = py5.frame_count * 0.015
    
    py5.rotate_x(py5.PI/4 + np.sin(t*0.5)*0.1)
    py5.rotate_z(py5.PI/4 + py5.frame_count * 0.002)
    
    py5.translate(-W/2, -H/2, 0)
    
    for y in range(ROWS):
        for x in range(COLS):
            py5.push_matrix()
            
            # Position
            px = x * CELL_SIZE
            py = y * CELL_SIZE
            py5.translate(px, py, 0)
            
            # Noise-driven folding
            n = py5.os_noise(x * 0.1, y * 0.1, t)
            
            # Origami fold (hinge on X or Y axis based on grid parity)
            is_even = (x + y) % 2 == 0
            
            fold_angle = n * py5.PI * 0.75
            
            if is_even:
                py5.rotate_x(fold_angle)
            else:
                py5.rotate_y(fold_angle)
                
            # Draw brutalist panel
            py5.fill(160, 160, 165) # Raw Concrete
            
            # Draw safety orange edges occasionally
            if py5.random(1) < 0.05:
                py5.stroke(255, 100, 0) # Safety Orange
                py5.stroke_weight(4)
            else:
                py5.stroke(40, 40, 45) # Deep shadow line
                py5.stroke_weight(1.5)
                
            # Draw panel (a thick box)
            py5.translate(CELL_SIZE/2, CELL_SIZE/2, 0)
            py5.box(CELL_SIZE * 0.95, CELL_SIZE * 0.95, 20)
            
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
