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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_branch(length, depth, max_depth, time):
    if depth > max_depth:
        return
        
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 8, 1))
    
    hue = (200 + depth * 15 + time * 50) % 360
    py5.stroke(hue, 80, 100, 50)
    
    py5.line(0, 0, 0, -length)
    py5.translate(0, -length)
    
    # Base angle variation
    angle_variation = np.sin(time + depth * 0.5) * 0.3
    
    if depth < max_depth:
        # Right branch
        py5.push_matrix()
        py5.rotate(0.5 + angle_variation)
        draw_branch(length * 0.7, depth + 1, max_depth, time)
        py5.pop_matrix()
        
        # Left branch
        py5.push_matrix()
        py5.rotate(-0.5 + angle_variation)
        draw_branch(length * 0.7, depth + 1, max_depth, time)
        py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Rotate the whole thing slowly
    py5.rotate(time * 0.1)
    
    # Draw 4 main trunks outward
    for i in range(4):
        py5.push_matrix()
        py5.rotate(i * py5.TWO_PI / 4)
        draw_branch(300, 0, 10, time)
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
