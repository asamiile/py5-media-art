from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.ADD)

def branch(length, depth, max_depth, angle_offset, time):
    if depth == 0:
        return
        
    py5.stroke(140 - depth * 10, 80, 100, 150)
    py5.stroke_weight(depth * 0.5)
    py5.line(0, 0, 0, -length)
    py5.translate(0, -length)
    
    # Wind sway
    sway = py5.os_noise(depth * 0.1, time * 0.01) * 0.5 - 0.25
    
    # Growth animation
    growth = min(1.0, max(0.0, (time - (max_depth - depth) * 10) * 0.05))
    
    if growth > 0:
        py5.push_matrix()
        py5.rotate(angle_offset + sway)
        branch(length * 0.75 * growth, depth - 1, max_depth, angle_offset, time)
        py5.pop_matrix()
        
        py5.push_matrix()
        py5.rotate(-angle_offset + sway)
        branch(length * 0.75 * growth, depth - 1, max_depth, angle_offset, time)
        py5.pop_matrix()
        
        # Center branch occasionally
        if depth % 2 == 0:
            py5.push_matrix()
            py5.rotate(sway * 1.5)
            branch(length * 0.6 * growth, depth - 1, max_depth, angle_offset, time)
            py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 10, 15)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height)
    branch(400, 10, 10, py5.PI / 6, py5.frame_count)

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
            
        import os
        os._exit(0)

py5.run_sketch()
