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
STAR_COUNT = 800
VOXELS = []

def grow_voxels(x, y, z, size, depth):
    if depth > 4 or (depth > 1 and np.random.rand() < 0.4):
        VOXELS.append({
            "pos": (x, y, z),
            "size": size,
            "color": np.random.randint(0, 3)
        })
        return
    
    # Try growing in 3 random directions (out of 6)
    dirs = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
    np.random.shuffle(dirs)
    for i in range(2):
        dx, dy, dz = dirs[i]
        new_size = size * np.random.uniform(0.6, 0.9)
        grow_voxels(x + dx * size * 0.5, y + dy * size * 0.5, z + dz * size * 0.5, new_size, depth + 1)

stars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    
    # Grow multiple structures
    for _ in range(5):
        cx = np.random.uniform(-400, 400)
        cy = np.random.uniform(-400, 400)
        cz = np.random.uniform(-400, 400)
        grow_voxels(cx, cy, cz, 200, 0)
        
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(-2000, 2000), np.random.uniform(-2000, 2000), np.random.uniform(-2000, 2000), np.random.uniform(50, 200)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Update Camera
    py5.background(2, 2, 5)
    py5.ambient_light(50, 50, 80)
    py5.directional_light(200, 200, 255, 1, 1, -1)
    
    # Camera rotation
    angle = py5.frame_count * 0.005
    cam_dist = 1200 + np.sin(t * py5.TWO_PI) * 200
    py5.camera(cam_dist * np.cos(angle), -400 + np.sin(angle)*200, cam_dist * np.sin(angle), 0, 0, 0, 0, 1, 0)
    
    # 2. Draw Stars
    py5.push_matrix()
    py5.no_stroke()
    for sx, sy, sz, s_alpha in stars:
        py5.push_matrix()
        py5.translate(sx, sy, sz)
        py5.fill(255, s_alpha)
        # Use simple box for stars in P3D
        py5.box(2)
        py5.pop_matrix()
    py5.pop_matrix()

    # 3. Draw Voxels
    py5.blend_mode(py5.ADD)
    for v in VOXELS:
        py5.push_matrix()
        x, y, z = v["pos"]
        py5.translate(x, y, z)
        
        # Breathing scale
        s_mult = 1.0 + np.sin(py5.frame_count * 0.05 + x) * 0.05
        py5.scale(s_mult)
        
        # Base material
        py5.fill(30, 30, 50, 180)
        py5.stroke_weight(1.0)
        
        if v["color"] == 0: # Cyan
            py5.stroke(0, 255, 255, 150)
        elif v["color"] == 1: # Amethyst
            py5.stroke(200, 100, 255, 150)
        else: # Gold
            py5.stroke(255, 200, 50, 150)
            
        py5.box(v["size"])
        
        # Internal core glow
        py5.no_stroke()
        py5.fill(255, 255, 255, 30)
        py5.box(v["size"] * 0.5)
        
        py5.pop_matrix()
    py5.blend_mode(py5.BLEND)

    # 4. Capture
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.6):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
