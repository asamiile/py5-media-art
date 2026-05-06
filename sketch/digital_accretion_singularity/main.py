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
MIN_R = 100
MAX_R = 800
MAX_LEVEL = 5

def generate_polar_quadtree(r1, r2, t1, t2, level):
    dr = r2 - r1
    dt = t2 - t1
    if level >= MAX_LEVEL or (dr > 20 and dt > 0.1 and np.random.random() > 0.6):
        # Generate a block
        height = np.random.uniform(5, 50 * (1 - level/MAX_LEVEL))
        return [(r1, r2, t1, t2, height, level)]
    
    mid_r = (r1 + r2) / 2
    mid_t = (t1 + t2) / 2
    blocks = []
    blocks.extend(generate_polar_quadtree(r1, mid_r, t1, mid_t, level + 1))
    blocks.extend(generate_polar_quadtree(mid_r, r2, t1, mid_t, level + 1))
    blocks.extend(generate_polar_quadtree(r1, mid_r, mid_t, t2, level + 1))
    blocks.extend(generate_polar_quadtree(mid_r, r2, mid_t, t2, level + 1))
    return blocks

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global blocks, stars
    blocks = generate_polar_quadtree(MIN_R, MAX_R, 0, py5.TWO_PI, 0)
    stars = np.random.uniform(-4000, 4000, (4000, 3))

def draw():
    py5.background(0, 0, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Camera
    cam_y = -400 + py5.sin(time_val * 0.3) * 100
    cam_dist = 1000 + py5.cos(time_val * 0.2) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), cam_y, cam_dist * py5.sin(time_val * 0.1), 0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Digital Accretion Disk
    py5.blend_mode(py5.ADD)
    for r1, r2, t1, t2, h, level in blocks:
        # Keplerian rotation speed: omega ~ r^-1.5
        avg_r = (r1 + r2) / 2
        rot_speed = 20.0 / (avg_r**1.5)
        angle_offset = time_val * rot_speed * 50.0
        
        ta, tb = t1 + angle_offset, t2 + angle_offset
        
        # Calculate 8 corners
        rs = [r1, r2, r2, r1]
        ts = [ta, ta, tb, tb]
        
        # Vertical shift near singularity
        y_offset = (100.0 / (avg_r/100.0)) # Bends downwards
        
        def to_cart(r, t, y):
            # Lensing factor
            lens = 1.0 + 40000.0 / (r*r + 10.0)
            return r * lens * np.cos(t), y - y_offset, r * lens * np.sin(t)

        corners_top = [to_cart(rs[i], ts[i], -h) for i in range(4)]
        corners_bottom = [to_cart(rs[i], ts[i], 0) for i in range(4)]
        
        # Color based on radius (heating)
        # Inner = Magenta/White, Outer = Cyan
        if avg_r < 300:
            py5.stroke(255, 0, 255, 120)
        else:
            py5.stroke(0, 255, 255, 80)
            
        py5.stroke_weight(1)
        py5.no_fill()
        
        # Draw edges
        py5.begin_shape()
        for p in corners_top: py5.vertex(*p)
        py5.end_shape(py5.CLOSE)
        
        py5.begin_shape()
        for p in corners_bottom: py5.vertex(*p)
        py5.end_shape(py5.CLOSE)
        
        for i in range(4):
            py5.line(*corners_top[i], *corners_bottom[i])
            
    py5.blend_mode(py5.BLEND)
    
    # 3. Central Event Horizon
    py5.fill(0)
    py5.no_stroke()
    py5.sphere(80)
    
    # Atmospheric glow of the singularity
    for i in range(2):
        py5.fill(200, 0, 255, 20)
        py5.sphere(90 + i * 20)

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
