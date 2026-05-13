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

# Simulation Parameters
NUM_PARTICLES = 1200
COULOMB_K = 1000.0  # Repulsion strength
TRAP_K = 0.05       # Harmonic trap strength
DAMPING = 0.95      # Velocity damping
MAX_TEMP = 2.5      # Maximum noise level at the end

# State
pos = None
vel = None
colors = None

def setup():
    global pos, vel, colors
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles in a circular region with some noise
    r = np.random.uniform(0, 400, (NUM_PARTICLES,))
    theta = np.random.uniform(0, py5.TWO_PI, (NUM_PARTICLES,))
    pos = np.stack([
        r * np.cos(theta) + SIZE[0] / 2,
        r * np.sin(theta) + SIZE[1] / 2
    ], axis=1).astype(np.float32)
    
    vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    
    # Colors: Electric Ice -> Neon Amethyst
    colors = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    for i in range(NUM_PARTICLES):
        colors[i] = [np.random.uniform(150, 200), np.random.uniform(200, 255), 255] # Cyan/Blue

def draw():
    global pos, vel
    py5.background(5, 5, 15) # Deep Indigo
    
    # 1. Physics Update (Vectorized)
    # Relative positions
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :] # (N, N, 2)
    dist_sq = np.sum(diff**2, axis=2) + 100.0 # (N, N) Avoid division by zero
    dist = np.sqrt(dist_sq)
    
    # Coulomb force: F = k * r / r^3
    force_mag = COULOMB_K / (dist_sq * dist) # (N, N)
    force_vec = diff * force_mag[:, :, np.newaxis] # (N, N, 2)
    total_force = np.sum(force_vec, axis=1) # (N, 2)
    
    # Trap force: F = -k * (pos - center)
    center = np.array([SIZE[0]/2, SIZE[1]/2])
    trap_force = -TRAP_K * (pos - center)
    
    # Temperature/Noise
    # Increases over time to melt the crystal
    temp = py5.remap(py5.frame_count, 0, TOTAL_FRAMES, 0.05, MAX_TEMP)
    noise = np.random.uniform(-1, 1, (NUM_PARTICLES, 2)) * temp
    
    # Integrate
    vel += (total_force + trap_force + noise)
    vel *= DAMPING
    pos += vel
    
    # 2. Rendering
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    
    # Draw glow particles
    for i in range(NUM_PARTICLES):
        # Color based on frame count (melting transition)
        t = py5.remap(py5.frame_count, 0, TOTAL_FRAMES, 0, 1)
        # Shift from Ice Blue to Amethyst
        r = py5.lerp(100, 200, t)
        g = py5.lerp(200, 50, t)
        b = py5.lerp(255, 255, t)
        
        # Subtle alpha flicker
        a = np.random.uniform(50, 150)
        
        py5.fill(r, g, b, a)
        # Draw central star
        py5.circle(pos[i, 0], pos[i, 1], 2)
        
        # Draw halo
        py5.fill(r, g, b, a * 0.2)
        py5.circle(pos[i, 0], pos[i, 1], 6)

    # 3. Save Frame and Video Export
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure we are in the right directory for ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        # Save mid-frame as preview
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
