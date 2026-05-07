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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 220000
SPEED_MIN = 30.0
SPEED_MAX = 50.0
OSCILLATION_FREQ = 0.2
STAR_COUNT = 12000

# State
pos = None
vel = None
phases = None
flavors = None
starfield = None


def setup():
    global pos, vel, phases, flavors, starfield
    py5.size(*SIZE)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize Neutrinos
    # Start slightly off-screen to the left/bottom
    pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    pos[:, 0] = np.random.uniform(-SIZE[0]*0.1, SIZE[0]*0.5, NUM_PARTICLES)
    pos[:, 1] = np.random.uniform(SIZE[1]*0.5, SIZE[1]*1.1, NUM_PARTICLES)
    
    # High-speed trajectories (mostly diagonal up-right)
    vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    angles = np.random.uniform(-np.pi/6, -np.pi/3, NUM_PARTICLES) # Towards upper right
    speeds = np.random.uniform(SPEED_MIN, SPEED_MAX, NUM_PARTICLES)
    vel[:, 0] = np.cos(angles) * speeds
    vel[:, 1] = np.sin(angles) * speeds
    
    phases = np.random.uniform(0, 2*np.pi, NUM_PARTICLES)
    flavors = np.random.uniform(0.5, 1.5, NUM_PARTICLES) # speed of oscillation
    
    # Starfield
    starfield = np.zeros((STAR_COUNT, 3), dtype=np.float32)
    starfield[:, 0] = np.random.uniform(0, SIZE[0], STAR_COUNT)
    starfield[:, 1] = np.random.uniform(0, SIZE[1], STAR_COUNT)
    starfield[:, 2] = np.random.uniform(20, 100, STAR_COUNT) # Brightness


def draw():
    global pos
    py5.background(5, 10, 5) # Deep near-black obsidian
    
    # Draw Starfield
    py5.stroke_weight(1)
    py5.stroke(200, 5, 80, 50)
    py5.points(starfield[:, :2])
    
    # Update Particles
    pos += vel
    
    # Wrap particles
    mask_x = pos[:, 0] > SIZE[0] * 1.1
    mask_y = pos[:, 1] < -SIZE[1] * 0.1
    mask_to_reset = mask_x | mask_y
    if np.any(mask_to_reset):
        num_reset = np.sum(mask_to_reset)
        pos[mask_to_reset, 0] = np.random.uniform(-SIZE[0]*0.2, 0, num_reset)
        pos[mask_to_reset, 1] = np.random.uniform(SIZE[1], SIZE[1]*1.2, num_reset)

    # Quantum Flavor Oscillation
    t = py5.frame_count * OSCILLATION_FREQ
    osc = np.sin(t * flavors + phases) # -1 to 1
    
    py5.blend_mode(py5.ADD)
    
    # Bin 1: Cyan
    mask1 = osc < -0.3
    py5.stroke(190, 80, 90, 20)
    py5.stroke_weight(1.5)
    py5.points(pos[mask1])
    
    # Bin 2: Amethyst
    mask2 = (osc >= -0.3) & (osc < 0.6)
    py5.stroke(280, 70, 80, 15)
    py5.stroke_weight(1.2)
    py5.points(pos[mask2])
    
    # Bin 3: Gold
    mask3 = osc >= 0.6
    py5.stroke(45, 90, 100, 30)
    py5.stroke_weight(2.0)
    py5.points(pos[mask3])
    
    py5.blend_mode(py5.BLEND)

    # Core Emitter Glow (bottom left)
    py5.no_stroke()
    for i in range(5):
        alpha = 20 - i*4
        size = 200 + i*150
        py5.fill(190, 40, 100, alpha)
        py5.ellipse(0, SIZE[1], size, size)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
