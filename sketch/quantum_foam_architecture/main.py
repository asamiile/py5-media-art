from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
QUANTA_COUNT = 40000
STAR_COUNT = 3000
VOLUME_SIZE = 800

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points, stars
    points = np.random.uniform(-VOLUME_SIZE/2, VOLUME_SIZE/2, (QUANTA_COUNT, 3))
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    py5.background(0, 0, 15)
    
    time_val = py5.frame_count / 60.0
    
    # Camera
    cam_dist = 1000 + py5.sin(time_val * 0.1) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Quantum Foam
    scale = 0.005
    # Vectorized noise sampling is hard in py5.noise, so we sample a subset or use chunks
    # To keep it interactive/fluid, we'll use a 3D Simplex-like approximation or fewer samples
    
    # Let's sample noise for each point
    # We'll use a subset of points for the "links" to keep it fast
    active_mask = []
    for p in points:
        n = py5.noise(p[0]*scale, p[1]*scale, p[2]*scale + time_val * 0.5)
        active_mask.append(n > 0.6)
    active_mask = np.array(active_mask)
    
    p_active = points[active_mask]
    
    py5.blend_mode(py5.ADD)
    
    # Render Active Quanta
    py5.stroke_weight(3)
    py5.stroke(0, 255, 255, 150) # Cyan
    py5.points(p_active)
    
    # Render Mesh Links (Proximity)
    # To optimize, we'll only link a subset of points
    py5.stroke_weight(1)
    py5.stroke(138, 43, 226, 60) # Violet
    py5.begin_shape(py5.LINES)
    # Simple proximity check in chunks
    max_link_dist = 50
    for i in range(0, len(p_active), 20):
        p1 = p_active[i]
        for j in range(i + 1, min(i + 100, len(p_active))):
            p2 = p_active[j]
            d = np.linalg.norm(p1 - p2)
            if d < max_link_dist:
                py5.vertex(*p1)
                py5.vertex(*p2)
    py5.end_shape()
    
    # Random Boxes for "Architecture"
    for i in range(0, len(p_active), 500):
        p = p_active[i]
        py5.push_matrix()
        py5.translate(*p)
        py5.stroke(255, 255, 255, 80)
        py5.stroke_weight(1)
        py5.no_fill()
        py5.box(py5.random(10, 30))
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "10M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
