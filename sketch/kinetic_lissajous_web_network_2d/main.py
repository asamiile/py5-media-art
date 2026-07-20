from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Pre-generate node properties to ensure they loop perfectly over TOTAL_FRAMES
num_nodes = 80
nodes = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    
    # We want a perfect loop. Each node will trace a Lissajous curve.
    # The frequencies must be integers to guarantee a full cycle at t=1.0.
    for i in range(num_nodes):
        nodes.append({
            "freq_x": random.randint(1, 4),
            "freq_y": random.randint(1, 4),
            "phase_x": random.uniform(0, py5.TWO_PI),
            "phase_y": random.uniform(0, py5.TWO_PI),
            "amp_x": random.uniform(py5.width * 0.1, py5.width * 0.45),
            "amp_y": random.uniform(py5.height * 0.1, py5.height * 0.45),
            "hue": random.choice([160, 180, 200, 320]) # Cyberpunk cyan, electric blue, and a little neon pink
        })

def draw():
    py5.background(190, 90, 5) # Extremely dark blue/cyan background
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Calculate current node positions
    current_positions = []
    for node in nodes:
        x = py5.width / 2 + math.sin(t * py5.TWO_PI * node["freq_x"] + node["phase_x"]) * node["amp_x"]
        y = py5.height / 2 + math.sin(t * py5.TWO_PI * node["freq_y"] + node["phase_y"]) * node["amp_y"]
        current_positions.append((x, y, node["hue"]))
        
    max_dist = 400.0
    
    # Draw connections
    py5.blend_mode(py5.ADD)
    py5.stroke_cap(py5.ROUND)
    
    for i in range(num_nodes):
        x1, y1, h1 = current_positions[i]
        for j in range(i + 1, num_nodes):
            x2, y2, h2 = current_positions[j]
            
            d = math.hypot(x2 - x1, y2 - y1)
            
            if d < max_dist:
                # Closer = brighter and thicker
                alpha = py5.remap(d, 0, max_dist, 100, 0)
                weight = py5.remap(d, 0, max_dist, 5, 0.5)
                
                # Interpolate hue between the two nodes
                h = py5.lerp(h1, h2, 0.5)
                
                py5.stroke(h, 90, 90, alpha)
                py5.stroke_weight(weight)
                py5.line(x1, y1, x2, y2)
                
    # Draw the nodes themselves as bright glowing dots
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    for x, y, h in current_positions:
        py5.fill(h, 60, 100)
        py5.ellipse(x, y, 12, 12)
        py5.fill(255)
        py5.ellipse(x, y, 4, 4)

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
        import os
        os._exit(0)

py5.run_sketch()
