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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE) # 2D only!
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw_quadtree(x, y, w, h, depth, max_depth, attractors):
    # Check if any attractor is inside this region
    should_subdivide = False
    for ax, ay in attractors:
        if x <= ax <= x + w and y <= ay <= y + h:
            should_subdivide = True
            break
            
    if should_subdivide and depth < max_depth:
        # Subdivide
        hw, hh = w / 2, h / 2
        draw_quadtree(x, y, hw, hh, depth + 1, max_depth, attractors)
        draw_quadtree(x + hw, y, hw, hh, depth + 1, max_depth, attractors)
        draw_quadtree(x, y + hh, hw, hh, depth + 1, max_depth, attractors)
        draw_quadtree(x + hw, y + hh, hw, hh, depth + 1, max_depth, attractors)
    else:
        # Draw this region
        # Stroke color depends on depth
        hue = py5.remap(depth, 0, max_depth, 180, 320)
        py5.stroke(hue, 80, 100, 50)
        py5.stroke_weight(py5.remap(depth, 0, max_depth, 4, 1))
        
        # Fill only deep regions
        if depth > max_depth - 2:
            py5.fill(hue, 80, 100, 20)
        else:
            py5.no_fill()
            
        # Draw with slight margin
        margin = py5.remap(depth, 0, max_depth, 10, 1)
        py5.rect(x + margin, y + margin, w - margin*2, h - margin*2)

def draw():
    # Motion blur background
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Calculate attractor positions based on time
    time = py5.frame_count * 0.02
    cx, cy = py5.width / 2, py5.height / 2
    
    attractors = []
    num_attractors = 5
    for i in range(num_attractors):
        offset = i * py5.TWO_PI / num_attractors
        r = py5.remap(py5.sin(time * 0.5 + offset), -1, 1, py5.height * 0.1, py5.height * 0.45)
        ax = cx + py5.cos(time + offset * 2) * r
        ay = cy + py5.sin(time * 1.3 + offset) * r
        attractors.append((ax, ay))
        
    draw_quadtree(0, 0, py5.width, py5.height, 0, 8, attractors)
    
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
