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
PARTICLE_COUNT = 180000
STAR_COUNT = 3000
ATTRACTOR_COUNT = 4

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global r, theta, h, attractors, stars
    # Distribution: thicker in the middle, thin at edges
    u = np.random.uniform(0, 1, PARTICLE_COUNT)
    r = 150 + 600 * np.sqrt(u)
    theta = np.random.uniform(0, py5.TWO_PI, PARTICLE_COUNT)
    h = np.random.normal(0, 10, PARTICLE_COUNT) * (1 - r/800.0)
    
    # Attractors: (radius, current_theta, speed, mass)
    attractors = []
    for i in range(ATTRACTOR_COUNT):
        ar = 200 + i * 120
        at = np.random.uniform(0, py5.TWO_PI)
        aspeed = 5.0 / (ar**1.5)
        amass = np.random.uniform(2, 5)
        attractors.append([ar, at, aspeed, amass])
        
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    global r, theta, attractors
    py5.background(5, 5, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Update Attractors
    for a in attractors:
        a[1] += a[2] # update theta
    
    # Update Particles
    # 1. Keplerian Rotation
    v_theta = 5.0 / (r**1.5)
    theta += v_theta
    
    # 2. Attraction / Clumping
    for ar, at, aspeed, amass in attractors:
        # Distance to attractor in polar
        dt = theta - at
        # Pull r and theta towards attractor
        pull = amass / (1.0 + (r - ar)**2 / 1000.0 + (dt**2)*500.0)
        r += (ar - r) * pull * 0.05
        theta += (at - theta) * pull * 0.05
        
    # Cartesian positions
    x = r * np.cos(theta)
    z = r * np.sin(theta)
    pos = np.stack([x, h, z], axis=1)
    
    # Camera
    cam_dist = 1000 + py5.sin(time_val * 0.1) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               -400 + 100 * py5.sin(time_val * 0.15), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Dust Disk
    py5.blend_mode(py5.ADD)
    # Color based on radius (heating)
    # Inner = Gold, Outer = Orange
    colors_idx = (r - 150) / 600.0
    
    # Sampling for speed (only render some groups)
    py5.stroke_weight(1)
    for i in range(3):
        mask = (colors_idx > i*0.33) & (colors_idx <= (i+1)*0.33)
        if i == 0: py5.stroke(255, 215, 0, 40) # Gold
        elif i == 1: py5.stroke(210, 105, 30, 30) # Orange
        else: py5.stroke(100, 50, 20, 20) # Deep Brown
        py5.points(pos[mask])
        
    # 3. Planetesimal Cores
    for ar, at, aspeed, amass in attractors:
        px = ar * np.cos(at)
        pz = ar * np.sin(at)
        py5.push_matrix()
        py5.translate(px, 0, pz)
        py5.no_stroke()
        for i in range(2):
            py5.fill(255, 255, 255, 50)
            py5.sphere(5 + i * 5)
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)
    
    # 4. Central Proto-star
    py5.no_stroke()
    for i in range(3):
        py5.fill(255, 255, 200, 30)
        py5.sphere(30 + i * 20)

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
