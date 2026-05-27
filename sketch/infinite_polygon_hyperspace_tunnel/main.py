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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_RINGS = 60
NUM_SIDES = 8
Z_SPACING = 150

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    
    py5.blend_mode(py5.ADD)
    
    py5.no_fill()
    py5.stroke_weight(4)
    
    time = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Calculate global z-offset for infinite motion
    z_offset = (py5.frame_count * 25) % Z_SPACING
    
    for i in range(NUM_RINGS):
        z = -i * Z_SPACING + z_offset
        
        # Warp the tunnel path
        tx = np.sin(z * 0.002 + time) * 300
        ty = np.cos(z * 0.003 + time * 1.2) * 300
        
        py5.push_matrix()
        py5.translate(tx, ty, z)
        
        # Rotate each ring
        py5.rotate_z(z * 0.001 + time * 0.2)
        
        # Color based on depth and time
        hue = (i * 5 + time * 20) % 360
        # Restrict to cool colors: 150 (green) to 280 (purple)
        mapped_hue = py5.remap(hue, 0, 360, 150, 280)
        
        py5.stroke(mapped_hue, 90, 100, 80)
        
        radius = 400 + np.sin(z * 0.01 + time * 2) * 100
        
        py5.begin_shape()
        for j in range(NUM_SIDES):
            angle = j * py5.TWO_PI / NUM_SIDES
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            py5.vertex(x, y, 0)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

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
