from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.spatial import Voronoi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 600
points_base = None
phases = None

def setup():
    global points_base, phases
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    margin = 500
    points_base = np.random.rand(NUM_POINTS, 2) * np.array([SIZE[0] + 2*margin, SIZE[1] + 2*margin]) - margin
    phases = np.random.rand(NUM_POINTS, 2) * 2 * np.pi

def draw():
    global points_base, phases
    
    # We want a pure dark background, but with a slight fade
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 50)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    movement = np.stack([
        np.sin(phases[:, 0] + time) * 150,
        np.cos(phases[:, 1] + time * 0.8) * 150
    ], axis=-1)
    
    current_points = points_base + movement
    
    try:
        vor = Voronoi(current_points)
    except Exception:
        py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
        return
        
    vertices = vor.vertices
    ridge_vertices = vor.ridge_vertices
    
    segments = []
    for ridge in ridge_vertices:
        if ridge[0] != -1 and ridge[1] != -1:
            segments.append([vertices[ridge[0], 0], vertices[ridge[0], 1],
                             vertices[ridge[1], 0], vertices[ridge[1], 1]])
                             
    if len(segments) > 0:
        lines = np.array(segments)
        
        py5.stroke_weight(1)
        py5.stroke(163, 228, 215, 150) # Ice blue
        py5.lines(lines)
        
        py5.stroke_weight(3)
        py5.stroke(0, 255, 255, 60) # Neon cyan
        py5.lines(lines)
        
        py5.stroke_weight(8)
        py5.stroke(0, 255, 255, 15) # Outer glow
        py5.lines(lines)

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
