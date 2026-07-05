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
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(140, 60, 10) # Deep forest green
    FRAMES_DIR.mkdir(exist_ok=True)
    # Increase recursion limit just in case
    sys.setrecursionlimit(20000)

def draw_branch(length, depth, max_depth, time_val, base_x, base_y):
    if depth == 0:
        return
        
    # Calculate noise for wind
    # Wind effect is stronger at the tips and varies by vertical position
    wind = py5.noise(base_x * 0.002, base_y * 0.002, time_val) * 2.0 - 1.0
    wind_angle = wind * (0.05 * (max_depth - depth + 1))
    
    # Calculate branch properties
    # Trunk is thick and brown/dark, tips are thin and bright autumn colors
    ratio = depth / max_depth
    thickness = max(1.0, ratio * 15.0)
    
    hue = 20 + (1.0 - ratio) * 60 # 20 (red) to 80 (yellow/greenish)
    brightness = 30 + (1.0 - ratio) * 70
    
    py5.stroke(hue, 90, brightness, 90)
    py5.stroke_weight(thickness)
    
    # Draw current branch
    py5.line(0, 0, 0, -length)
    
    # Move to end of branch
    py5.translate(0, -length)
    
    # Next branch settings
    new_length = length * 0.75
    
    # Left branch
    py5.push_matrix()
    angle_l = -np.pi/6 + wind_angle + py5.noise(depth, time_val*1.5) * 0.1
    py5.rotate(angle_l)
    # Recursion
    draw_branch(new_length, depth - 1, max_depth, time_val, base_x, base_y - length)
    py5.pop_matrix()
    
    # Right branch
    py5.push_matrix()
    angle_r = np.pi/6 + wind_angle + py5.noise(depth+100, time_val*1.5) * 0.1
    py5.rotate(angle_r)
    # Recursion
    draw_branch(new_length, depth - 1, max_depth, time_val, base_x, base_y - length)
    py5.pop_matrix()


def draw():
    py5.blend_mode(py5.BLEND)
    # Motion blur
    py5.no_stroke()
    py5.fill(140, 60, 10, 25)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.015
    
    py5.push_matrix()
    # Start at bottom center
    py5.translate(py5.width / 2, py5.height)
    
    # Base trunk
    max_depth = 12
    initial_length = py5.height * 0.25
    
    draw_branch(initial_length, max_depth, max_depth, time_val, py5.width/2, py5.height)
    
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
