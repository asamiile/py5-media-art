from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

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

rects = []
edges = []

def subdivide(x, y, w, h, depth):
    if depth == 0 or (depth < 6 and random.random() < 0.3):
        rects.append((x, y, w, h))
        return
        
    hw = w / 2
    hh = h / 2
    subdivide(x, y, hw, hh, depth - 1)
    subdivide(x + hw, y, hw, hh, depth - 1)
    subdivide(x, y + hh, hw, hh, depth - 1)
    subdivide(x + hw, y + hh, hw, hh, depth - 1)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    random.seed(42)
    py5.random_seed(42)
    
    # Generate quadtree
    padding = 100
    subdivide(padding, padding, py5.width - padding*2, py5.height - padding*2, 6)
    
    # Generate edges
    for r in rects:
        x, y, w, h = r
        edges.append({'x1': x, 'y1': y, 'x2': x+w, 'y2': y}) # top
        edges.append({'x1': x+w, 'y1': y, 'x2': x+w, 'y2': y+h}) # right
        edges.append({'x1': x+w, 'y1': y+h, 'x2': x, 'y2': y+h}) # bottom
        edges.append({'x1': x, 'y1': y+h, 'x2': x, 'y2': y}) # left

def draw():
    py5.background(0, 0, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # Draw static circuit board
    py5.stroke(180, 80, 20, 50)
    py5.stroke_weight(1)
    py5.no_fill()
    for r in rects:
        x, y, w, h = r
        py5.rect(x, y, w, h)
        
    # Draw data streams
    py5.stroke_weight(3)
    
    for i, e in enumerate(edges):
        x1, y1, x2, y2 = e['x1'], e['y1'], e['x2'], e['y2']
        dist = py5.dist(x1, y1, x2, y2)
        
        # Determine active edges based on noise
        activity = py5.os_noise(i * 0.1, t * 0.5)
        if activity > 0.3:
            hue = (200 + i * 0.1 + t * 50) % 360
            py5.stroke(hue, 90, 100, 90)
            
            # Draw moving segment
            # Segment travels from (x1, y1) to (x2, y2)
            progress = (t * 2 + i * 0.1) % 1.0
            
            # segment length
            seg_len = min(dist, 50)
            seg_prog = progress * dist
            
            start_dist = max(0, seg_prog - seg_len)
            end_dist = seg_prog
            
            dx = (x2 - x1) / dist if dist > 0 else 0
            dy = (y2 - y1) / dist if dist > 0 else 0
            
            sx = x1 + dx * start_dist
            sy = y1 + dy * start_dist
            ex = x1 + dx * end_dist
            ey = y1 + dy * end_dist
            
            py5.line(sx, sy, ex, ey)
            
            # Draw node at the end of some active edges
            if progress > 0.9 and dist > 0:
                py5.fill(hue, 90, 100)
                py5.no_stroke()
                py5.circle(ex, ey, 8)

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
