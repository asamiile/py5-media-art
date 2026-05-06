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
STAR_COUNT = 1000
BACKGROUND_STAR_COUNT = 5000
TRAIL_LENGTH = 15

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global stars, bg_stars, trails
    # Orbital parameters: a, e, i, Omega, omega, theta
    a = np.random.uniform(50, 600, STAR_COUNT)
    e = np.random.uniform(0.3, 0.95, STAR_COUNT)
    i = np.random.uniform(0, py5.PI, STAR_COUNT)
    Omega = np.random.uniform(0, py5.TWO_PI, STAR_COUNT)
    omega = np.random.uniform(0, py5.TWO_PI, STAR_COUNT)
    theta = np.random.uniform(0, py5.TWO_PI, STAR_COUNT)
    
    # Store parameters in a NumPy array
    stars = np.stack([a, e, i, Omega, omega, theta], axis=1)
    
    # Pre-calculate rotation matrices or components
    # We'll calculate positions in draw() to keep it simple but vectorized
    
    # Background stars
    bg_stars = np.random.uniform(-3000, 3000, (BACKGROUND_STAR_COUNT, 3))
    
    # Trails: circular buffer for each star
    trails = np.zeros((STAR_COUNT, TRAIL_LENGTH, 3))

def get_orbital_pos(params):
    a, e, i, Omega, omega, theta = params.T
    
    # Radial distance
    r = a * (1 - e**2) / (1 + e * np.cos(theta))
    
    # Position in orbital plane
    x_p = r * np.cos(theta)
    y_p = r * np.sin(theta)
    
    # 3D rotation
    cos_O = np.cos(Omega)
    sin_O = np.sin(Omega)
    cos_o = np.cos(omega)
    sin_o = np.sin(omega)
    cos_i = np.cos(i)
    sin_i = np.sin(i)
    
    # Transformation matrices elements
    x = x_p * (cos_O * cos_o - sin_O * sin_o * cos_i) - y_p * (cos_O * sin_o + sin_O * cos_o * cos_i)
    y = x_p * (sin_O * cos_o + cos_O * sin_o * cos_i) - y_p * (sin_O * sin_o - cos_O * cos_o * cos_i)
    z = x_p * (sin_o * sin_i) + y_p * (cos_o * sin_i)
    
    return np.stack([x, y, z], axis=1)

def draw():
    global stars, trails
    py5.background(0, 0, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Update orbital angles
    # Speed is proportional to 1/r^1.5 (Kepler's 3rd law)
    a = stars[:, 0]
    e = stars[:, 1]
    theta = stars[:, 5]
    r = a * (1 - e**2) / (1 + e * np.cos(theta))
    d_theta = 2.0 / (r**1.5) # Arbitrary factor for visual speed
    stars[:, 5] += d_theta
    
    # Calculate new positions
    current_pos = get_orbital_pos(stars)
    
    # Update trails
    trails = np.roll(trails, 1, axis=1)
    trails[:, 0, :] = current_pos
    
    # Camera
    cam_dist = 1200 + py5.sin(time_val * 0.15) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Background Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in bg_stars:
        py5.point(*s)
        
    # 2. S-Stars and Trails (Additive)
    py5.blend_mode(py5.ADD)
    for i in range(STAR_COUNT):
        # Determine color based on velocity (r)
        # Faster (smaller r) = Whiter/Brighter
        r_val = np.linalg.norm(current_pos[i])
        alpha = py5.lerp(255, 50, r_val / 600.0)
        
        # Draw Trail
        py5.no_fill()
        py5.stroke_weight(1.5)
        py5.begin_shape()
        for j in range(TRAIL_LENGTH):
            t_pos = trails[i, j]
            if np.all(t_pos == 0): continue
            # Gradient alpha for trail
            t_alpha = alpha * (1.0 - j / TRAIL_LENGTH)
            py5.stroke(255, 255, 200, t_alpha)
            py5.vertex(*t_pos)
        py5.end_shape()
        
        # Draw Star Core
        py5.stroke_weight(3)
        py5.stroke(255, 255, 255, alpha)
        py5.point(*current_pos[i])
        
    py5.blend_mode(py5.BLEND)
    
    # 3. Central Void
    py5.fill(0)
    py5.no_stroke()
    py5.sphere(30)

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
