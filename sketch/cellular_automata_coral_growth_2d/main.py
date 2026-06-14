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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def branch(length, angle_offset, depth, time):
    if depth == 0:
        return
        
    py5.stroke_weight(depth * 1.5)
    
    # Calculate color based on depth and time
    hue = (time * 20 + depth * 30) % 360
    py5.stroke(hue, 80, 100, 80)
    
    # Draw the branch
    py5.line(0, 0, 0, -length)
    py5.translate(0, -length)
    
    # Branching factor with some noise for organic movement
    noise_val1 = py5.os_noise(depth * 0.1, time * 0.5) - 0.5
    noise_val2 = py5.os_noise(depth * 0.1 + 10, time * 0.5) - 0.5
    
    angle1 = angle_offset + noise_val1 * py5.PI / 4
    angle2 = -angle_offset + noise_val2 * py5.PI / 4
    
    new_length = length * 0.7
    
    py5.push_matrix()
    py5.rotate(angle1)
    branch(new_length, angle_offset, depth - 1, time)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate(angle2)
    branch(new_length, angle_offset, depth - 1, time)
    py5.pop_matrix()

def draw():
    py5.background(15, 80, 15)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    # Draw multiple fractal coral structures
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1])
    branch(400, py5.PI / 6, 11, time)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(SIZE[0]/4, SIZE[1])
    py5.rotate(py5.PI/8)
    branch(250, py5.PI / 5, 9, time + 5)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(SIZE[0]*3/4, SIZE[1])
    py5.rotate(-py5.PI/8)
    branch(300, py5.PI / 7, 10, time + 10)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
