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
PARTICLE_COUNT = 200000
STAR_COUNT = 4000

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colors, stars
    # Initial positions in a cylindrical volume
    r = np.random.uniform(0, 400, PARTICLE_COUNT)
    theta = np.random.uniform(0, py5.TWO_PI, PARTICLE_COUNT)
    z = np.random.uniform(-1000, 1000, PARTICLE_COUNT)
    
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    pos = np.stack([x, y, z], axis=1)
    
    # Colors: Teal and Amethyst
    colors = np.zeros((PARTICLE_COUNT, 3))
    mask = np.random.random(PARTICLE_COUNT) > 0.5
    colors[mask] = [0, 150, 150] # Teal
    colors[~mask] = [150, 80, 200] # Amethyst
    
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    global pos
    py5.background(0, 0, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Update particles using a braided vector field
    # Vectorized rotation and drift
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    
    # Rotation speed varies with z to create "braiding"
    d_theta = 0.02 * np.sin(z * 0.002 + time_val * 0.5)
    cos_dt = np.cos(d_theta)
    sin_dt = np.sin(d_theta)
    
    # Apply rotation matrix
    new_x = x * cos_dt - y * sin_dt
    new_y = x * sin_dt + y * cos_dt
    
    # Update z with wrap
    z += 2.0
    z[z > 1000] = -1000
    
    # Update positions
    pos[:, 0] = new_x
    pos[:, 1] = new_y
    pos[:, 2] = z
    
    # Camera
    cam_dist = 1200 + py5.sin(time_val * 0.2) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Filaments (Additive)
    py5.blend_mode(py5.ADD)
    # Render Teal group
    teal_mask = (colors[:, 0] == 0)
    py5.stroke(0, 128, 128, 40)
    py5.stroke_weight(2)
    py5.points(pos[teal_mask])
    py5.stroke(200, 255, 255, 20)
    py5.stroke_weight(1)
    py5.points(pos[teal_mask])
    
    # Render Amethyst group
    py5.stroke(150, 80, 200, 40)
    py5.stroke_weight(2)
    py5.points(pos[~teal_mask])
    py5.stroke(255, 200, 255, 20)
    py5.stroke_weight(1)
    py5.points(pos[~teal_mask])
    
    py5.blend_mode(py5.BLEND)
    
    # Add a central "energy pulse" glow
    py5.push_matrix()
    py5.no_stroke()
    for i in range(2):
        py5.fill(150, 100, 255, 10)
        py5.sphere(100 + i * 100)
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
