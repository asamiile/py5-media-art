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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Smoothly morphing parameters for the Peter de Jong Attractor
    a = np.interp(np.sin(t * py5.TWO_PI), [-1, 1], [-2.5, 2.5])
    b = np.interp(np.cos(t * py5.TWO_PI * 1.3), [-1, 1], [-2.5, 2.5])
    c = np.interp(np.sin(t * py5.TWO_PI * 0.7), [-1, 1], [-2.5, 2.5])
    d = np.interp(np.cos(t * py5.TWO_PI * 1.1), [-1, 1], [-2.5, 2.5])
    
    # We will generate a lot of points using vectorized numpy
    num_particles = 150_000
    
    # For performance, we'll do 10 iterations to generate the dust
    x = np.random.uniform(-2, 2, num_particles)
    y = np.random.uniform(-2, 2, num_particles)
    
    # Iteration step
    for _ in range(8):
        x_new = np.sin(a * y) - np.cos(b * x)
        y_new = np.sin(c * x) - np.cos(d * y)
        x = x_new
        y = y_new
        
    # Scale and translate to fit screen
    scale_factor = py5.height * 0.22
    px = py5.width / 2 + x * scale_factor
    py_coord = py5.height / 2 + y * scale_factor
    
    # Combine positions
    verts = np.column_stack((px, py_coord))
    
    # Draw points
    py5.no_fill()
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    
    py5.stroke(150, 100, 255, 30)
    py5.vertices(verts)
    
    py5.end_shape()
    
    # Add a glowing center pass with cyan
    py5.stroke(50, 200, 255, 15)
    py5.stroke_weight(2)
    # We just reuse the same vertices but shift them slightly to create a glow
    glow_verts = verts + np.random.normal(0, 3, size=verts.shape)
    
    py5.begin_shape(py5.POINTS)
    py5.vertices(glow_verts)
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
