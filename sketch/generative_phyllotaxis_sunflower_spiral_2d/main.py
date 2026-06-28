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

NUM_SEEDS = 40000
GOLDEN_ANGLE = 137.5077640500378546463487 * np.pi / 180.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global indices
    indices = np.arange(1, NUM_SEEDS + 1)

def draw():
    # Motion blur / fading trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 60)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Dynamic expansion coefficient based on time
    c = 8.0 + np.sin(t * py5.TWO_PI) * 2.0
    
    # Calculate angles with a continuous rotation over time
    theta = indices * GOLDEN_ANGLE + (t * py5.TWO_PI * 3.0)
    
    # Add a slight wave/wobble to the radius
    wobble = np.sin(indices * 0.01 + t * py5.TWO_PI * 2.0) * 2.0
    
    # Calculate radius
    r = c * np.sqrt(indices) + wobble
    
    # Convert polar to Cartesian
    cx, cy = py5.width / 2, py5.height / 2
    x = cx + r * np.cos(theta)
    y = cy + r * np.sin(theta)
    
    # Create vertices array
    points = np.column_stack((x, y))
    
    # Divide into 3 color groups based on radius to emulate glowing layers
    group1 = r < (py5.height * 0.2)
    group2 = (r >= (py5.height * 0.2)) & (r < (py5.height * 0.4))
    group3 = r >= (py5.height * 0.4)
    
    py5.stroke_weight(py5.width * 0.003)
    
    # Inner: Neon Yellow/White
    py5.stroke(255, 255, 100, 200)
    py5.begin_shape(py5.POINTS)
    py5.vertices(points[group1])
    py5.end_shape()
    
    # Middle: Neon Orange/Pink
    py5.stroke(255, 100, 50, 200)
    py5.begin_shape(py5.POINTS)
    py5.vertices(points[group2])
    py5.end_shape()
    
    # Outer: Deep Magenta/Purple
    py5.stroke(200, 50, 255, 200)
    py5.begin_shape(py5.POINTS)
    py5.vertices(points[group3])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
