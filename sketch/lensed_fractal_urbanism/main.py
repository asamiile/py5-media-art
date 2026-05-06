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
MIN_SIZE = 20
MAX_LEVEL = 6
EINSTEIN_RADIUS = 300
CITY_SIZE = 2000

def generate_quadtree(x, z, size, level):
    if level >= MAX_LEVEL or (size > MIN_SIZE and np.random.random() > 0.7):
        # Generate a block
        height = np.random.uniform(20, 400 * (1 - level/MAX_LEVEL))
        return [(x, z, size, height, level)]
    
    half = size / 2
    blocks = []
    blocks.extend(generate_quadtree(x - half/2, z - half/2, half, level + 1))
    blocks.extend(generate_quadtree(x + half/2, z - half/2, half, level + 1))
    blocks.extend(generate_quadtree(x - half/2, z + half/2, half, level + 1))
    blocks.extend(generate_quadtree(x + half/2, z + half/2, half, level + 1))
    return blocks

def apply_lensing(pos, center):
    v = pos - center
    d2 = np.sum(v**2, axis=1, keepdims=True)
    d = np.sqrt(d2)
    # Lensing shift
    shift = 1.0 + (EINSTEIN_RADIUS**2) / (d2 + 10.0)
    return center + v * shift

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global blocks, stars
    blocks = generate_quadtree(0, 0, CITY_SIZE, 0)
    stars = np.random.uniform(-4000, 4000, (3000, 3))

def draw():
    py5.background(0, 0, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Camera
    cam_x = py5.sin(time_val * 0.2) * 800
    cam_z = py5.cos(time_val * 0.1) * 800
    py5.camera(cam_x, -600, cam_z, 0, 0, 0, 0, 1, 0)
    
    # Light source for shadow feel
    py5.ambient_light(50, 50, 80)
    py5.point_light(200, 200, 255, 0, -1000, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Lensed City
    # We lens each block's vertices
    center = np.array([0, 0, 0])
    
    py5.blend_mode(py5.ADD)
    for x, z, size, h, level in blocks:
        # Define 8 corners of the box
        half = size / 2
        corners = np.array([
            [x-half, -h, z-half], [x+half, -h, z-half], [x+half, -h, z+half], [x-half, -h, z+half],
            [x-half, 0, z-half], [x+half, 0, z-half], [x+half, 0, z+half], [x-half, 0, z+half]
        ])
        
        # Warp corners
        # For simplicity in 3D, we warp in the X-Z plane relative to origin
        warped = corners.copy()
        xz_warped = apply_lensing(corners[:, [0, 2]], center[[0, 2]])
        warped[:, [0, 2]] = xz_warped
        
        # Color based on level
        if level % 2 == 0:
            py5.stroke(0, 255, 255, 100) # Cyan
        else:
            py5.stroke(255, 0, 255, 100) # Magenta
            
        py5.stroke_weight(1)
        py5.no_fill()
        
        # Draw the warped box edges
        # Top face
        py5.begin_shape()
        for i in range(4): py5.vertex(*warped[i])
        py5.end_shape(py5.CLOSE)
        
        # Bottom face
        py5.begin_shape()
        for i in range(4, 8): py5.vertex(*warped[i])
        py5.end_shape(py5.CLOSE)
        
        # Vertical edges
        for i in range(4):
            py5.line(*warped[i], *warped[i+4])
            
    py5.blend_mode(py5.BLEND)
    
    # 3. Central "Singularity" Glow
    py5.push_matrix()
    py5.no_stroke()
    for i in range(3):
        py5.fill(255, 255, 255, 20)
        py5.sphere(50 + i * 20)
    py5.pop_matrix()

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
