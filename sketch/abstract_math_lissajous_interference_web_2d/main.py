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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters for the 5 Lissajous figures
NUM_FIGURES = 5
POINTS_PER_FIGURE = 15000

# Base parameters
frequencies_x = np.array([3.0, 5.0, 7.0, 11.0, 13.0])
frequencies_y = np.array([2.0, 4.0, 6.0, 10.0, 12.0])

phases_x = np.random.rand(NUM_FIGURES) * py5.PI * 2
phases_y = np.random.rand(NUM_FIGURES) * py5.PI * 2

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global t_array
    # Parametric t values for drawing the curves
    t_array = np.linspace(0, py5.PI * 40, POINTS_PER_FIGURE)
    
def draw():
    # Subtle background fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1)
    
    progress = py5.frame_count / TOTAL_FRAMES
    # Organic pulsing size
    global_size = (py5.height * 0.4) * (1.0 + 0.1 * np.sin(progress * py5.PI * 2))
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # 5 different colors
    colors = [
        (255, 50, 150, 15), # Pink
        (50, 200, 255, 15), # Cyan
        (255, 200, 50, 15), # Gold
        (150, 50, 255, 15), # Purple
        (50, 255, 100, 15)  # Green
    ]
    
    # Draw all 5 figures
    for i in range(NUM_FIGURES):
        # Dynamically shift parameters
        a = frequencies_x[i] + 0.5 * np.sin(progress * py5.PI * 2 + i)
        b = frequencies_y[i] + 0.5 * np.cos(progress * py5.PI * 2 + i)
        
        delta_x = phases_x[i] + progress * py5.PI * 2
        delta_y = phases_y[i] - progress * py5.PI * 2
        
        # Calculate parametric points
        x = np.sin(a * t_array + delta_x) * global_size
        y = np.sin(b * t_array + delta_y) * global_size
        
        # Combine into lines
        pts = np.column_stack((x, y))
        
        # Rotate entire figure slowly
        rot = progress * py5.PI * 2 * (1 if i % 2 == 0 else -1)
        c, s = np.cos(rot), np.sin(rot)
        rot_mat = np.array([[c, -s], [s, c]])
        pts = np.dot(pts, rot_mat)
        
        py5.stroke(*colors[i])
        
        # We need pairs of points for py5.lines()
        # Like: pt0, pt1, pt1, pt2, pt2, pt3...
        # Using a fast numpy stride trick
        lines = np.empty((POINTS_PER_FIGURE - 1, 2, 2))
        lines[:, 0, :] = pts[:-1]
        lines[:, 1, :] = pts[1:]
        
        # Flatten to 2D array of (num_lines, 4) for py5.lines()
        line_coords = lines.reshape(-1, 4)
        
        py5.lines(line_coords)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
