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

# Simulation parameters
NUM_PARTICLES = 70000
# [r, angle, height, velocity]
particles_polar = np.zeros((NUM_PARTICLES, 4))
# Store positions for rendering
particles_pos = np.zeros((NUM_PARTICLES, 3))

def setup():
    global particles_polar, particles_pos
    py5.size(*SIZE, py5.P3D)
    py5.background(0, 0, 2)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize accretion disk particles
    # Radius between 100 and 450
    r = np.random.uniform(90, 480, NUM_PARTICLES)
    angle = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    # Thicker disk with Gaussian height
    height = np.random.normal(0, 1, NUM_PARTICLES) * (r / 5)
    
    # Keplerian velocity
    v = 60.0 / (np.sqrt(r) * 1.5)
    
    particles_polar[:, 0] = r
    particles_polar[:, 1] = angle
    particles_polar[:, 2] = height
    particles_polar[:, 3] = v

def draw():
    global particles_polar, particles_pos
    py5.background(0, 0, 3)
    
    t = py5.frame_count / FPS
    
    # Background starfield with dramatic gravitational lensing
    np.random.seed(42)
    cx, cy = SIZE[0]//2, SIZE[1]//2
    rs = 75.0 # Schwarzschild radius for lensing
    
    for _ in range(600):
        x_orig, y_orig = np.random.uniform(-SIZE[0]*0.5, SIZE[0]*1.5), np.random.uniform(-SIZE[1]*0.5, SIZE[1]*1.5)
        z_star = np.random.uniform(-1500, -800)
        
        dx, dy = x_orig - cx, y_orig - cy
        dist = np.sqrt(dx*dx + dy*dy)
        
        # Einstein Ring distortion
        if dist > rs * 0.8:
            # Warp factor (r' = r + rs^2/r)
            factor = (dist + (rs**2 / dist)) / dist
            x, y = cx + dx * factor, cy + dy * factor
            
            s = np.random.uniform(0.5, 2.0)
            alpha = np.random.uniform(20, 60)
            # Twinkle
            alpha *= (0.7 + 0.3 * np.sin(t * 2 + x_orig))
            
            py5.stroke(0, 0, 100, alpha)
            py5.stroke_weight(s)
            py5.point(x, y, z_star)
    np.random.seed(None)

    # Einstein Ring Glow
    py5.no_fill()
    for i in range(10):
        alpha = 15 - i
        py5.stroke(200, 40, 100, alpha) # Faint cyan glow
        py5.stroke_weight(2)
        py5.circle(cx, cy, rs*2 + i*2)

    # Singularity shadow
    py5.no_stroke()
    py5.fill(0, 0, 0, 100)
    py5.push_matrix()
    py5.translate(cx, cy, 0)
    py5.sphere(rs)
    py5.pop_matrix()

    # Update accretion disk
    particles_polar[:, 1] += particles_polar[:, 3]
    
    # Conversion to Cartesian
    r = particles_polar[:, 0]
    angle = particles_polar[:, 1]
    h = particles_polar[:, 2]
    
    particles_pos[:, 0] = r * np.cos(angle)
    particles_pos[:, 1] = h
    particles_pos[:, 2] = r * np.sin(angle)
    
    # Rendering
    py5.push_matrix()
    py5.translate(cx, cy, 0)
    py5.rotate_x(py5.radians(80))
    py5.rotate_z(t * 0.03)
    
    # Disk coloring: Cyan inside, Orange outside
    # Doppler shift: hue shifts based on sine(angle)
    # Inner (90) to Outer (480)
    # Hue: 190 (Cyan) to 25 (Orange)
    h_base = py5.remap(r, 90, 480, 190, 25)
    doppler = np.sin(angle) * 20
    hues = (h_base + doppler) % 360
    
    # Use fewer batches for speed
    for h_target in range(20, 221, 20):
        mask = (hues >= h_target) & (hues < h_target + 20)
        if np.any(mask):
            # Saturation increases towards orange
            sat = py5.remap(h_target, 20, 200, 90, 60)
            py5.stroke(h_target, sat, 100, 30)
            py5.stroke_weight(1.2)
            py5.points(particles_pos[mask])
    
    py5.pop_matrix()

    # Save frames and exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
