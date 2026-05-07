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
JET_SPEED = 15.0
PRECESSION_SPEED = 0.5
CONE_ANGLE = 0.4 # Radians

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, age, stars
    pos = np.zeros((PARTICLE_COUNT, 3))
    vel = np.zeros((PARTICLE_COUNT, 3))
    age = np.random.uniform(0, 100, PARTICLE_COUNT)
    
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    global pos, vel, age
    py5.background(0, 0, 10)
    
    time_val = py5.frame_count / 60.0
    
    # 1. Update Jet Direction (Precession)
    angle = time_val * PRECESSION_SPEED * py5.TWO_PI
    # Bipolar jet axis
    axis = np.array([np.sin(CONE_ANGLE) * np.cos(angle),
                     np.sin(CONE_ANGLE) * np.sin(angle),
                     np.cos(CONE_ANGLE)])
    
    # 2. Recycle and Update Particles
    # Move
    pos += vel
    age += 1.0
    
    # Recycle dead particles
    dead_mask = (age > 100) | (np.linalg.norm(pos, axis=1) > 1200)
    num_dead = np.sum(dead_mask)
    if num_dead > 0:
        pos[dead_mask] = 0
        age[dead_mask] = 0
        
        # Bipolar emission
        directions = axis if np.random.random() > 0.5 else -axis
        noise = np.random.normal(0, 0.05, (num_dead, 3))
        vel[dead_mask] = (directions + noise) * JET_SPEED
        
    # Camera
    cam_dist = 1200 + py5.sin(time_val * 0.1) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.15), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Relativistic Jets
    py5.blend_mode(py5.ADD)
    
    # Color based on age/distance
    # Teal at center, Violet at edges
    dist = np.linalg.norm(pos, axis=1)
    colors_idx = dist / 1200.0
    
    # Render in chunks for alpha/color variety
    for i in range(2):
        if i == 0:
            mask = (colors_idx < 0.5)
            py5.stroke(0, 200, 255, 40) # Teal
            py5.stroke_weight(2)
        else:
            mask = (colors_idx >= 0.5)
            py5.stroke(150, 50, 255, 30) # Violet
            py5.stroke_weight(1)
            
        py5.points(pos[mask])
        
    # 3. Central Core
    py5.push_matrix()
    py5.no_stroke()
    for i in range(3):
        py5.fill(255, 255, 255, 30 / (i+1))
        py5.sphere(10 + i * 15)
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
