from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Constants
NUM_PARTICLES = 150_000
NUM_STARS = 12_000

# State
pos = None # x, y, z
state = None # internal oscillator state (-1 or 1 roughly)
stars = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, state, stars
    
    # Initialize Particles in a 3D grid/block
    # We use a random distribution but contained in a volume
    pos = np.random.uniform(-800, 800, (NUM_PARTICLES, 3))
    # Oscillators are mostly along X axis
    state = np.random.uniform(-1, 1, NUM_PARTICLES)
    
    # Initialize Stars
    stars = np.random.uniform(-3000, 3000, (NUM_STARS, 3))

def update_physics():
    global state, pos
    t = py5.frame_count / FPS
    
    # Double-well potential dynamics: dx/dt = x - x^3 + noise + A*cos(wt)
    # Vectorized update
    dt = 0.1
    noise_strength = 0.6
    forcing_amp = 0.4
    forcing_freq = 0.5 # Slow pulse
    
    # Force from potential V(x) = -x^2/2 + x^4/4 => -V' = x - x^3
    force = state - state**3
    
    # Periodic Forcing
    signal = forcing_amp * np.cos(t * forcing_freq * np.pi * 2)
    
    # Noise
    noise = np.random.normal(0, noise_strength, NUM_PARTICLES)
    
    # Update State
    state += (force + signal + noise) * dt
    
    # Map state to visual offset (displacement along X)
    pos[:, 0] = (pos[:, 0] % 1600) - 800 + state * 20.0
    
    # Slow drift
    pos[:, 1] += np.sin(t * 0.2 + pos[:, 0] * 0.001) * 2.0
    pos[:, 2] += np.cos(t * 0.3 + pos[:, 1] * 0.001) * 2.0

def draw():
    update_physics()
    
    py5.background(5, 2, 12) # Deep indigo
    
    py5.translate(py5.width/2, py5.height/2, -1200)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.001)
    
    # Draw Stars
    py5.stroke(200, 220, 255, 70)
    py5.stroke_weight(1.0)
    py5.points(stars)
    
    # Draw Resonance Lattice
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 1.0)
    
    # We color based on state (which well they are in)
    # Well A (negative)
    mask_a = (state < 0)
    py5.stroke_weight(1.5)
    py5.stroke(185, 80, 100, 0.25) # Electric Cyan
    py5.points(pos[mask_a])
    
    # Well B (positive)
    mask_b = (state >= 0)
    py5.stroke_weight(1.5)
    py5.stroke(285, 75, 100, 0.25) # Deep Amethyst
    py5.points(pos[mask_b])
    
    # Transitions (high velocity / center)
    mask_c = (np.abs(state) < 0.2)
    py5.stroke_weight(2.0)
    py5.stroke(200, 5, 100, 0.4) # Neon White
    py5.points(pos[mask_c])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        py5.blend_mode(py5.BLEND)
        py5.color_mode(py5.RGB, 255)
        
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
