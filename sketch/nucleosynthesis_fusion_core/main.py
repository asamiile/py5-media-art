from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

# Add project root to path for lib imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Configuration
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 150000
# Elements: 0: H (Blue), 1: He (Amber), 2: C (Rose), 3: O (Violet)
pos = np.random.normal(0, 600, (NUM_PARTICLES, 3)).astype(np.float32)
vel = np.random.normal(0, 2, (NUM_PARTICLES, 3)).astype(np.float32)
element = np.zeros(NUM_PARTICLES, dtype=np.int32)
age = np.random.uniform(0, 100, NUM_PARTICLES).astype(np.float32)

# Fusion events (gamma streaks)
MAX_STREAKS = 500
streak_pos = np.zeros((MAX_STREAKS, 3), dtype=np.float32)
streak_vel = np.zeros((MAX_STREAKS, 3), dtype=np.float32)
streak_life = np.zeros(MAX_STREAKS, dtype=np.float32)
streak_ptr = 0

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global pos, vel, element, age, streak_ptr
    f = py5.frame_count
    
    py5.background(15, 5, 10) # Deep plasma red tint
    
    # Camera
    py5.translate(py5.width / 2, py5.height / 2, -1000)
    py5.rotate_x(f * 0.005)
    py5.rotate_y(f * 0.003)
    
    # Convection field + Central Gravity
    dist = np.sqrt(np.sum(pos**2, axis=1))
    dist = np.clip(dist, 1, None)
    
    # Force towards center (softened gravity)
    softening = 10000
    gravity_mag = 500 / (dist**2 + softening)
    gravity = -pos * (gravity_mag[:, np.newaxis])
    
    # Convection: Toroidal rotation + Radial pulse
    # Normalized rotation to prevent runaway at large radii
    convection = np.zeros_like(pos)
    convection[:, 0] = -pos[:, 1] / dist * 2
    convection[:, 1] = pos[:, 0] / dist * 2
    convection[:, 2] = np.sin(dist * 0.01 + f * 0.1) * 3 # Radial pulse
    
    vel += gravity + convection
    vel *= 0.95 # Stronger damping for stability
    pos += vel
    
    # Keep particles within a reasonable volume
    pos = np.clip(pos, -2000, 2000)
    
    # Fusion Logic (Stylized)
    # If two particles are very close, they might fuse
    # For performance, we'll just use a probability-based fusion for particles near the center
    fuse_prob = np.exp(-dist / 100) * 0.001
    mask = (np.random.rand(NUM_PARTICLES) < fuse_prob) & (element < 3)
    
    if np.any(mask):
        fusing_indices = np.where(mask)[0]
        element[mask] += 1
        # Create gamma streaks
        for idx in fusing_indices[:10]: # Limit streaks per frame
            streak_pos[streak_ptr] = pos[idx]
            streak_vel[streak_ptr] = (pos[idx] / dist[idx]) * 20 # Outward burst
            streak_life[streak_ptr] = 1.0
            streak_ptr = (streak_ptr + 1) % MAX_STREAKS

    # Render Particles
    # Color mapping
    colors = [
        (100, 200, 255), # H: Neon Blue
        (255, 200, 100), # He: Amber
        (255, 100, 150), # C: Rose
        (200, 150, 255)  # O: Violet
    ]
    
    # Sub-sample for performance and aesthetics
    # We use py5.points(numpy_array) which is much faster than a loop
    for e_type in range(4):
        idx = np.where(element == e_type)[0]
        if len(idx) == 0: continue
        r, g, b = colors[e_type]
        py5.stroke(r, g, b, 200)
        py5.stroke_weight(2.5)
        # Using vectorized points()
        py5.points(pos[idx[::2]])
    
    # Render Gamma Streaks
    py5.stroke_weight(2)
    for i in range(MAX_STREAKS):
        if streak_life[i] > 0:
            py5.stroke(255, 255, 255, 255 * streak_life[i])
            start = streak_pos[i]
            end = start + streak_vel[i] * 2
            py5.line(*start, *end)
            streak_pos[i] += streak_vel[i]
            streak_life[i] -= 0.05

    # Core Glow
    py5.no_stroke()
    for i in range(3):
        alpha = 50 - i * 15
        py5.fill(255, 100, 50, alpha)
        py5.sphere(100 + i * 50)

    # Video & Preview Save
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if f >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error during video encoding: {e}")

if __name__ == "__main__":
    py5.run_sketch()
