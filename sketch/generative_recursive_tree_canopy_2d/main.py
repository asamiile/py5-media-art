from pathlib import Path
import shutil
import subprocess
import sys
import math
import random
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw_branch(length, depth, t, x_offset):
    if depth == 0:
        # Draw a leaf or bloom
        py5.no_stroke()
        hue = (100 + depth * 20 + py5.frame_count * 0.5) % 360
        py5.fill(hue, 80, 100, 200)
        leaf_size = length * 1.5 * (1 + math.sin(t * 2 + x_offset))
        py5.circle(0, 0, leaf_size)
        return

    # Draw branch
    py5.stroke(40, 60, 40) # Brown-ish
    py5.stroke_weight(depth * 1.5)
    py5.line(0, 0, 0, -length)
    
    py5.translate(0, -length)
    
    # Calculate wind sway using noise
    # Based on depth and overall time
    wind = py5.remap(py5.os_noise(x_offset * 0.01, depth * 0.1, t * 0.5), 0, 1, -0.3, 0.3)
    
    # Left branch
    py5.push_matrix()
    angle_left = math.pi / 6 + wind + math.sin(t + depth) * 0.1
    py5.rotate(-angle_left)
    draw_branch(length * 0.75, depth - 1, t, x_offset - length)
    py5.pop_matrix()
    
    # Right branch
    py5.push_matrix()
    angle_right = math.pi / 5 - wind + math.cos(t + depth) * 0.1
    py5.rotate(angle_right)
    draw_branch(length * 0.7, depth - 1, t, x_offset + length)
    py5.pop_matrix()

def draw():
    py5.background(20, 80, 15)
    
    t = py5.frame_count * 0.02
    
    # Draw several trees
    num_trees = 5
    spacing = py5.width / (num_trees + 1)
    
    for i in range(1, num_trees + 1):
        py5.push_matrix()
        py5.translate(i * spacing, py5.height)
        
        # Give each tree a slightly different starting wind offset based on position
        draw_branch(py5.height * 0.25, 9, t, i * spacing)
        
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
