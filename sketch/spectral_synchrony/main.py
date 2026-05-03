import subprocess
from pathlib import Path
import sys
import numpy as np
import py5

# Standard imports for the repo
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

# Kuramoto Parameters
NUM_OSCILLATORS = 200
COUPLING_STRENGTH = 1.2
NEIGHBOR_RADIUS = 200.0

class Oscillator:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.phase = np.random.uniform(0, py5.TWO_PI)
        self.natural_freq = np.random.normal(1.0, 0.2)
        self.current_freq = self.natural_freq

def setup():
    global oscillators
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize oscillators in a grid with some jitter
    w, h = SIZE
    cols = 15
    rows = 14
    oscillators = []
    for i in range(cols):
        for j in range(rows):
            ox = (i + 0.5) * (w / cols) + np.random.normal(0, 20)
            oy = (j + 0.5) * (h / rows) + np.random.normal(0, 20)
            oscillators.append(Oscillator(ox, oy))


def draw():
    global oscillators
    py5.background(20, 20, 20)
    py5.blend_mode(py5.SCREEN)
    
    # 1. Update phases (Kuramoto Model)
    dt = 0.05
    new_phases = []
    
    # Use NumPy for distance calculations
    positions = np.array([[o.x, o.y] for o in oscillators])
    phases = np.array([o.phase for o in oscillators])
    
    for i, o in enumerate(oscillators):
        # Calculate distances to all other oscillators
        dists = np.linalg.norm(positions - positions[i], axis=1)
        
        # Coupling with neighbors
        neighbors = (dists < NEIGHBOR_RADIUS) & (dists > 0)
        if np.any(neighbors):
            # dTheta/dt = omega + (K/N) * sum(sin(theta_j - theta_i))
            coupling = (COUPLING_STRENGTH / np.sum(neighbors)) * np.sum(np.sin(phases[neighbors] - o.phase))
            d_phase = (o.natural_freq + coupling) * dt
        else:
            d_phase = o.natural_freq * dt
            
        new_phases.append((o.phase + d_phase) % py5.TWO_PI)
        
    for i, o in enumerate(oscillators):
        o.phase = new_phases[i]

    # 2. Draw connections
    py5.stroke_weight(0.8)
    for i, o1 in enumerate(oscillators):
        for j in range(i + 1, len(oscillators)):
            o2 = oscillators[j]
            dx = o1.x - o2.x
            dy = o1.y - o2.y
            dist_sq = dx*dx + dy*dy
            if dist_sq < NEIGHBOR_RADIUS * NEIGHBOR_RADIUS:
                dist = np.sqrt(dist_sq)
                # Coherence: 1.0 if phases are identical
                coherence = 0.5 + 0.5 * np.cos(o1.phase - o2.phase)
                
                if coherence > 0.8:
                    alpha = (coherence - 0.8) * 5.0 * 100 * (1.0 - dist / NEIGHBOR_RADIUS)
                    # Electric cyan for high coherence
                    py5.stroke(0, 255, 255, alpha)
                    py5.line(o1.x, o1.y, o2.x, o2.y)
                elif coherence < 0.2:
                    alpha = (0.2 - coherence) * 5.0 * 50 * (1.0 - dist / NEIGHBOR_RADIUS)
                    # Deep magenta for anti-phase
                    py5.stroke(139, 0, 139, alpha)
                    py5.line(o1.x, o1.y, o2.x, o2.y)

    # 3. Draw nodes
    for o in oscillators:
        # Pulse brightness based on phase
        brightness = 0.5 + 0.5 * np.sin(o.phase)
        py5.no_stroke()
        
        # Core
        py5.fill(0, 255, 255, 150 * brightness)
        py5.circle(o.x, o.y, 4 + 2 * brightness)
        
        # Glow
        py5.fill(50, 205, 50, 40 * brightness) # Phosphor green accent
        py5.circle(o.x, o.y, 12 + 8 * brightness)

    # Standard animation frame saving and video encoding
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


if __name__ == "__main__":
    py5.run_sketch()
