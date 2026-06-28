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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
MAX_DEPTH = 12

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(10, 5, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(length, depth, max_depth, global_time):
    # Base case
    if depth == 0:
        return
        
    # Draw the current branch
    # Stroke weight gets thinner towards the tips
    weight = py5.remap(depth, 1, max_depth, 0.5, 10.0)
    py5.stroke_weight(weight)
    
    # Color smoothly transitions from pink/purple at the base to glowing cyan at the tips
    progress = 1.0 - (depth / max_depth)
    r = 255 - 200 * progress
    g = 50 + 200 * progress
    b = 200 + 55 * progress
    
    # The tips glow brighter
    alpha = 255 if depth <= 3 else 150
    py5.stroke(r, g, b, alpha)
    
    py5.line(0, 0, 0, -length)
    
    # Move to the end of the branch
    py5.translate(0, -length)
    
    # The wind affects the tips more than the trunk
    # We use a 2D perlin noise field: noise(time, depth)
    wind_force = py5.noise(global_time * 0.5, depth * 0.1) * 2.0 - 1.0
    wind_angle = wind_force * (py5.PI / 8.0) * (progress ** 2.0)
    
    # Right branch
    py5.push_matrix()
    py5.rotate(py5.PI / 6.0 + wind_angle)
    draw_branch(length * 0.75, depth - 1, max_depth, global_time)
    py5.pop_matrix()
    
    # Left branch
    py5.push_matrix()
    py5.rotate(-py5.PI / 6.0 + wind_angle)
    draw_branch(length * 0.75, depth - 1, max_depth, global_time)
    py5.pop_matrix()

def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 5, 20, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global_time = py5.frame_count / 30.0
    
    # Draw a forest of 3 trees
    trees = [
        {"x": py5.width * 0.5, "y": py5.height * 0.95, "len": 350, "depth": 13, "scale": 1.0},
        {"x": py5.width * 0.2, "y": py5.height * 0.85, "len": 250, "depth": 11, "scale": 0.8},
        {"x": py5.width * 0.8, "y": py5.height * 0.85, "len": 250, "depth": 11, "scale": 0.8}
    ]
    
    for i, t in enumerate(trees):
        py5.push_matrix()
        py5.translate(t["x"], t["y"])
        # Offset time so each tree sways differently
        draw_branch(t["len"], t["depth"], t["depth"], global_time + i * 10.0)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
