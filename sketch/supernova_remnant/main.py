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
NUM_PARTICLES = 120000
particles = np.zeros((NUM_PARTICLES, 3))
velocities = np.zeros((NUM_PARTICLES, 3))
colors = np.zeros((NUM_PARTICLES, 3)) # RGB

def setup():
    global particles, velocities, colors
    py5.size(*SIZE, py5.P3D)
    py5.background(5, 5, 10)
    py5.color_mode(py5.RGB, 255)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles at the core with explosive velocities
    angles = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    phi = np.arccos(np.random.uniform(-1, 1, NUM_PARTICLES))
    r = np.random.uniform(0, 50, NUM_PARTICLES)
    
    particles[:, 0] = r * np.sin(phi) * np.cos(angles)
    particles[:, 1] = r * np.sin(phi) * np.sin(angles)
    particles[:, 2] = r * np.cos(phi)
    
    # Initial "explosion" velocity
    speed = np.random.uniform(2, 10, NUM_PARTICLES)
    velocities[:, 0] = speed * np.sin(phi) * np.cos(angles)
    velocities[:, 1] = speed * np.sin(phi) * np.sin(angles)
    velocities[:, 2] = speed * np.cos(phi)
    
    # Colors: mix of Violet, Crimson, and White
    for i in range(NUM_PARTICLES):
        choice = np.random.random()
        if choice < 0.6: # Violet
            colors[i] = [138, 43, 226]
        elif choice < 0.9: # Crimson
            colors[i] = [220, 20, 60]
        else: # White
            colors[i] = [255, 255, 255]

def draw():
    global particles, velocities
    py5.background(5, 5, 15)
    
    t = py5.frame_count / FPS
    
    # Static starfield with fixed seed
    np.random.seed(42)
    py5.no_stroke()
    for _ in range(300):
        x, y = np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])
        z_star = np.random.uniform(-1000, 500)
        s = np.random.uniform(0.5, 2.5)
        alpha = np.random.uniform(50, 150) + 50 * np.sin(t * 0.5 + x)
        py5.fill(255, 255, 255, alpha)
        py5.push_matrix()
        py5.translate(x, y, z_star)
        py5.circle(0, 0, s)
        py5.pop_matrix()
    np.random.seed(None)

    # Core glow (fading)
    core_alpha = max(0, 200 - py5.frame_count * 1.5)
    if core_alpha > 0:
        py5.fill(255, 255, 200, core_alpha)
        py5.push_matrix()
        py5.translate(SIZE[0]//2, SIZE[1]//2, 0)
        py5.sphere(40)
        py5.pop_matrix()

    # Update particles
    # Add turbulence and drag
    # Note: noise is slow, we use a simple sine-based turbulence for performance
    noise_factor = 0.5 * np.exp(-t * 0.2)
    velocities[:, 0] += np.sin(particles[:, 1] * 0.01 + t) * noise_factor
    velocities[:, 1] += np.sin(particles[:, 2] * 0.01 + t * 0.8) * noise_factor
    velocities[:, 2] += np.sin(particles[:, 0] * 0.01 + t * 1.2) * noise_factor
    
    # Drag
    velocities *= 0.97
    
    particles += velocities
    
    # Rendering
    py5.push_matrix()
    py5.translate(SIZE[0]//2, SIZE[1]//2, 0)
    py5.rotate_y(t * 0.1)
    
    # Using np_pixels is hard in 3D, we'll use py5.points() but it's slow for 120k.
    # Actually, let's use py5.stroke() and py5.point() in a subset for speed if needed.
    # Or use vectorized points if possible? py5 doesn't have a vectorized point(X, Y, Z).
    # Wait, py5.points(coords) exists!
    
    # Split by color for performance and visibility
    # Violet
    v_mask = colors[:, 0] == 138
    # Glow layer
    py5.stroke_weight(3.0)
    py5.stroke(138, 43, 226, 40)
    py5.points(particles[v_mask])
    # Core layer
    py5.stroke_weight(1.0)
    py5.stroke(138, 43, 226, 200)
    py5.points(particles[v_mask])
    
    # Crimson
    c_mask = colors[:, 0] == 220
    # Glow layer
    py5.stroke_weight(3.0)
    py5.stroke(220, 20, 60, 50)
    py5.points(particles[c_mask])
    # Core layer
    py5.stroke_weight(1.0)
    py5.stroke(220, 20, 60, 220)
    py5.points(particles[c_mask])
    
    # White
    w_mask = colors[:, 0] == 255
    # Glow layer
    py5.stroke_weight(4.0)
    py5.stroke(255, 255, 255, 60)
    py5.points(particles[w_mask])
    # Core layer
    py5.stroke_weight(1.5)
    py5.stroke(255, 255, 255, 255)
    py5.points(particles[w_mask])
    
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
