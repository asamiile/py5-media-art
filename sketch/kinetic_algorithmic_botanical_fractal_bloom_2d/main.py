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

MAX_DEPTH = 8
BRANCHES = 6

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(5, 10, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_cap(py5.ROUND)

def draw_branch(length, depth, time_val):
    if depth == 0:
        return
        
    # Color based on depth and time
    hue = (140 + depth * 25 + time_val * 10) % 360
    # Pinkish tips
    if depth < 3:
        hue = (320 + time_val * 5) % 360
        
    brightness = 50 + (MAX_DEPTH - depth) * 5
    alpha = 20 + depth * 10
    
    py5.stroke(hue, 80, brightness, alpha)
    py5.stroke_weight(depth * 1.5)
    
    # Draw the branch
    py5.line(0, 0, 0, -length)
    
    # Move to the end of the branch
    py5.translate(0, -length)
    
    # Calculate angles that breathe
    angle1 = np.sin(time_val * 0.8 + depth * 0.3) * (np.pi / 4) + (np.pi / 6)
    angle2 = -np.cos(time_val * 0.7 - depth * 0.4) * (np.pi / 4) - (np.pi / 6)
    
    # Left branch
    py5.push_matrix()
    py5.rotate(angle1)
    draw_branch(length * 0.7, depth - 1, time_val)
    py5.pop_matrix()
    
    # Right branch
    py5.push_matrix()
    py5.rotate(angle2)
    draw_branch(length * 0.75, depth - 1, time_val)
    py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10, 15, 20) # Motion blur
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Rotate the whole flower slowly
    py5.rotate(time_val * 0.1)
    
    # Draw radially symmetric branches
    for i in range(BRANCHES):
        py5.push_matrix()
        py5.rotate((np.pi * 2 / BRANCHES) * i)
        # Add a little breathing to the starting length
        start_len = 350 + np.sin(time_val * 1.5) * 50
        draw_branch(start_len, MAX_DEPTH, time_val)
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

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
