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

# Dragon Curve L-System
axiom = "FX"
rules = {
    "X": "X+YF+",
    "Y": "-FX-Y"
}
iterations = 14

def generate_lsystem(axiom, rules, iterations):
    result = axiom
    for _ in range(iterations):
        next_result = []
        for char in result:
            next_result.append(rules.get(char, char))
        result = "".join(next_result)
    return result

sequence = ""
path_points = []
segments = []

def setup():
    global sequence, path_points, segments
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    sequence = generate_lsystem(axiom, rules, iterations)
    
    # Pre-calculate points to fit on screen
    x, y = 0.0, 0.0
    angle = 0.0
    step = 10.0
    
    path = [(x, y)]
    min_x, max_x = 0, 0
    min_y, max_y = 0, 0
    
    for cmd in sequence:
        if cmd == 'F':
            x += np.cos(angle) * step
            y += np.sin(angle) * step
            path.append((x, y))
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
        elif cmd == '+':
            angle += np.pi / 2
        elif cmd == '-':
            angle -= np.pi / 2
            
    # Normalize to screen
    w = max_x - min_x
    h = max_y - min_y
    scale = min(py5.width / w, py5.height / h) * 0.85
    
    cx = (max_x + min_x) / 2
    cy = (max_y + min_y) / 2
    
    offset_x = py5.width / 2 - cx * scale
    offset_y = py5.height / 2 - cy * scale
    
    for (px, py_pos) in path:
        nx = px * scale + offset_x
        ny = py_pos * scale + offset_y
        path_points.append((nx, ny))
        
    for i in range(len(path_points) - 1):
        segments.append((path_points[i], path_points[i+1]))

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Draw segments progressively
    progress = py5.frame_count / TOTAL_FRAMES
    # The curve draws over time, we show a sliding window "head"
    
    total_segments = len(segments)
    head_index = int(progress * total_segments * 1.5) # slightly faster to finish before end
    
    start_index = max(0, head_index - 300)
    end_index = min(head_index, total_segments)
    
    py5.stroke_weight(5.0)
    
    for i in range(start_index, end_index):
        p1 = segments[i][0]
        p2 = segments[i][1]
        
        # Color based on position along curve
        hue = (i / total_segments * 360 * 3 + py5.frame_count) % 360
        py5.stroke(hue, 90, 80, 80)
        py5.line(p1[0], p1[1], p2[0], p2[1])

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
