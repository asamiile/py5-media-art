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
PARTICLE_COUNT = 150000
STAR_COUNT = 4000
SHELL_WIDTH = 30.0
MAX_RADIUS = 1200

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, density, stars
    # Dust cloud particles in a large sphere
    phi = np.random.uniform(0, py5.TWO_PI, PARTICLE_COUNT)
    costheta = np.random.uniform(-1, 1, PARTICLE_COUNT)
    u = np.random.uniform(0, 1, PARTICLE_COUNT)
    
    theta = np.arccos(costheta)
    r = MAX_RADIUS * np.cbrt(u)
    
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    pos = np.stack([x, y, z], axis=1)
    
    # Pre-calculate density using noise
    # We'll sample noise in chunks for speed
    density = np.zeros(PARTICLE_COUNT)
    scale = 0.005
    for i in range(0, PARTICLE_COUNT, 1000):
        chunk = pos[i:i+1000]
        for j, p in enumerate(chunk):
            density[i+j] = py5.noise(p[0]*scale, p[1]*scale, p[2]*scale)
            
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    py5.background(5, 5, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Light shell radius (traveling at speed "c")
    shell_r = (time_val / DURATION_SEC) * MAX_RADIUS * 1.2
    
    # Camera
    cam_dist = 800 + py5.sin(time_val * 0.1) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Light Echo (Dust)
    # Calculate distance for all particles
    dist = np.linalg.norm(pos, axis=1)
    
    # Alpha based on proximity to the expanding shell
    # Gaussian-like thickness
    diff = np.abs(dist - shell_r)
    alpha_base = np.exp(-(diff**2) / (SHELL_WIDTH**2))
    
    # Final alpha: density * alpha_base
    final_alpha = density * alpha_base * 255
    
    # Filter particles to render only visible ones for speed
    mask = final_alpha > 5
    p_visible = pos[mask]
    a_visible = final_alpha[mask]
    
    py5.blend_mode(py5.ADD)
    # We can't use points() with per-point alpha easily in one call
    # but we can group them or just use a few points() calls with sampled alphas
    # To keep it silken and high quality:
    for a_val in [50, 150, 250]:
        a_mask = (a_visible >= a_val - 50) & (a_visible < a_val + 50)
        if np.any(a_mask):
            py5.stroke(0, 200, 255, a_val // 2)
            py5.stroke_weight(2)
            py5.points(p_visible[a_mask])
            
            py5.stroke(200, 255, 255, a_val // 4)
            py5.stroke_weight(1)
            py5.points(p_visible[a_mask])
            
    py5.blend_mode(py5.BLEND)
    
    # 3. Supernova Core
    core_alpha = 255 * np.exp(-time_val * 2.0) # Fades out fast
    if core_alpha > 1:
        py5.push_matrix()
        py5.no_stroke()
        for i in range(3):
            py5.fill(255, 255, 255, core_alpha / (i+1))
            py5.sphere(10 + i * 10)
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
