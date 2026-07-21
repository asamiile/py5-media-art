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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_grid(spacing, angle, phase):
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    py5.rotate(angle)
    # overscan to ensure it covers the screen while rotating
    diag = np.hypot(SIZE[0], SIZE[1])
    py5.translate(-diag, -diag)
    
    num_lines = int(diag * 2 / spacing)
    for i in range(num_lines):
        x = i * spacing + phase
        py5.line(x, 0, x, diag * 2)
    py5.pop_matrix()

def draw():
    py5.background(0)
    py5.blend_mode(py5.DIFFERENCE)
    py5.no_fill()
    py5.stroke_weight(4)
    
    t = py5.frame_count * 0.01
    
    # Layer 1: Concentric expanding circles
    py5.stroke(0, 255, 255) # Cyan
    spacing_circ = 40 + np.sin(t * 0.5) * 20
    phase_circ = (py5.frame_count * 2) % spacing_circ
    
    diag = np.hypot(SIZE[0]/2, SIZE[1]/2)
    num_circles = int(diag / spacing_circ) + 2
    for i in range(num_circles):
        r = i * spacing_circ + phase_circ
        py5.circle(SIZE[0]/2, SIZE[1]/2, r * 2)
        
    # Layer 2: Rotating Magenta Grid
    py5.stroke(255, 0, 255)
    angle_mag = t * 0.2 + np.sin(t * 0.3) * 0.5
    draw_grid(30, angle_mag, 0)
    
    # Layer 3: Rotating Yellow Grid
    py5.stroke(255, 255, 0)
    angle_yel = -t * 0.15 + np.cos(t * 0.4) * 0.5
    phase_yel = np.sin(t * 1.5) * 15
    draw_grid(35, angle_yel, phase_yel)

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
