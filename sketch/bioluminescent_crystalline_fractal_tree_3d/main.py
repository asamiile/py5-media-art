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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_branch(length, depth, max_depth, t, seed):
    if depth > max_depth:
        return
        
    # Stroke weight tapers off towards the tips
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 12, 1))
    
    # Hue goes from Violet (280) to Cyan (180)
    hue = py5.remap(depth, 0, max_depth, 280, 180)
    alpha = py5.remap(depth, 0, max_depth, 60, 100)
    py5.stroke(hue, 90, 100, alpha)
    
    py5.line(0, 0, 0, 0, -length, 0)
    
    py5.translate(0, -length, 0)
    
    next_length = length * 0.65
    
    # 4 branches branching out
    num_branches = 4
    for i in range(num_branches):
        with py5.push_matrix():
            # Sway based on noise
            angle_y = i * py5.TWO_PI / num_branches + t * 0.5 + py5.os_noise(seed, i, t*0.2)
            angle_z = py5.PI / 5 + py5.os_noise(seed, depth, t*0.5) * 0.4
            
            py5.rotate_y(angle_y)
            py5.rotate_z(angle_z)
            
            # Recursive call
            draw_branch(next_length, depth + 1, max_depth, t, seed + i * 10 + depth)

def draw():
    py5.background(10, 80, 5) # Very dark indigo/black
    py5.blend_mode(py5.ADD)
    
    # Set camera and position
    py5.translate(SIZE[0] / 2, SIZE[1] - 200, -500)
    
    t = py5.frame_count * 0.02
    
    # Slowly rotate the entire tree
    py5.rotate_y(t * 0.3)
    
    # Draw the crystalline tree
    draw_branch(500, 0, 6, t, 0)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
