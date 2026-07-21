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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    py5.blend_mode(py5.ADD)
    py5.no_fill()

def draw_polygon(x, y, radius, npoints):
    angle = py5.TWO_PI / npoints
    py5.begin_shape()
    for a in np.arange(0, py5.TWO_PI, angle):
        sx = x + np.cos(a) * radius
        sy = y + np.sin(a) * radius
        py5.vertex(sx, sy)
    py5.end_shape(py5.CLOSE)

def draw():
    # Very dark purple background (needs to be opaque so blend_mode(ADD) works over frames without trails)
    py5.blend_mode(py5.BLEND)
    py5.background(280, 80, 5) 
    
    py5.blend_mode(py5.ADD)
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    layers = 24
    
    for i in range(layers):
        layer_t = t + (i * 0.05)
        
        # Radius breathes and scales based on layer
        r = 200 + (i * 50) + np.sin(layer_t * py5.TWO_PI) * 150
        
        # Rotation varies for each layer
        rot = (layer_t * py5.TWO_PI) * (1.0 if i % 2 == 0 else -1.0) * ((i + 1) * 0.1)
        
        # Color palettes
        if i % 3 == 0:
            py5.stroke(320, 90, 80) # Neon pink
        elif i % 3 == 1:
            py5.stroke(180, 90, 80) # Cyan
        else:
            py5.stroke(45, 90, 80) # Gold
            
        py5.stroke_weight(py5.remap(np.sin(layer_t * py5.TWO_PI * 3), -1, 1, 1, 8))
        
        py5.push_matrix()
        py5.rotate(rot)
        draw_polygon(0, 0, r, 3 + (i % 6)) # Mix of triangles, squares, pentagons, etc.
        py5.pop_matrix()

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
        import os
        os._exit(0)

py5.run_sketch()
