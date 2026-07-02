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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

centers = []
colors = []

def setup():
    global centers, colors
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5)
    
    centers = [
        np.array([py5.width * 0.45, py5.height * 0.45]),
        np.array([py5.width * 0.55, py5.height * 0.55]),
        np.array([py5.width * 0.55, py5.height * 0.45]),
        np.array([py5.width * 0.45, py5.height * 0.55]),
    ]
    colors = [
        (255, 20, 40),   # Red/Pink
        (20, 255, 100),  # Green/Cyan
        (40, 60, 255),   # Blue
        (200, 180, 20),  # Yellow/Gold
    ]

def draw():
    py5.background(5)
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    max_radius = py5.dist(0, 0, py5.width, py5.height) * 1.5
    spacing = 16
    num_rings = int(max_radius / spacing)
    
    for i, c in enumerate(centers):
        cx = c[0] + py5.sin(t * (i + 1) * 0.7) * 200
        cy = c[1] + py5.cos(t * (i + 1) * 0.5) * 200
        
        py5.stroke(*colors[i])
        
        for r_idx in range(num_rings):
            # Outward expansion
            r = (r_idx * spacing + (py5.frame_count * 2.0)) % max_radius
            if r < 1: continue
            
            # Line thickness modulation for extra illusion effect
            mod = (py5.sin(r * 0.04 - t * 3) + 1) * 0.5
            py5.stroke_weight(1 + mod * 5)
            
            # Ellipse to create more complex interference than perfect circles
            rx = r * (1 + py5.sin(t * 0.2 + i) * 0.1)
            ry = r * (1 + py5.cos(t * 0.3 + i) * 0.1)
            
            py5.ellipse(cx, cy, rx * 2, ry * 2)
            
    py5.blend_mode(py5.BLEND)

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
