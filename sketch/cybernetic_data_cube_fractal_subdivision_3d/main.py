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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_fill()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_octree(x, y, z, size, depth, max_depth, t):
    # Determine if we should subdivide based on 4D noise
    noise_val = py5.os_noise(x * 0.003, y * 0.003, z * 0.003, t * 2.0)
    
    if depth < max_depth and noise_val > 0.4 + (depth * 0.05):
        s2 = size / 2.0
        s4 = size / 4.0
        # Subdivide into 8 children
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                for dz in [-1, 1]:
                    draw_octree(x + dx * s4, y + dy * s4, z + dz * s4, s2, depth + 1, max_depth, t)
    else:
        # Draw the leaf node
        if depth > 1:
            py5.push_matrix()
            py5.translate(x, y, z)
            
            # Pulse intensity based on depth and time
            pulse = py5.sin(t * py5.TWO_PI * 3.0 + x * 0.01 + y * 0.01) * 0.5 + 0.5
            
            if noise_val > 0.6:
                py5.stroke(180, 80, 100, 40 + pulse * 60) # Cyan
                py5.fill(180, 100, 100, 10 * pulse)
            elif noise_val < 0.4:
                py5.stroke(320, 80, 100, 40 + pulse * 60) # Magenta
                py5.fill(320, 100, 100, 10 * pulse)
            else:
                py5.stroke(240, 60, 80, 30) # Dim blue
                py5.no_fill()
                
            py5.stroke_weight(max(0.5, 3.0 - depth * 0.5))
            
            # Small scaling factor so boxes don't touch perfectly
            py5.box(size * 0.9)
            py5.pop_matrix()

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.rotate_x(t * py5.TWO_PI * 0.5)
    py5.rotate_y(t * py5.TWO_PI * 0.3)
    
    draw_octree(0, 0, 0, 800, 0, 5, t)

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
