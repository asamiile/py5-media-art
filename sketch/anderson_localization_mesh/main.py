from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 150000
GRID_RES = 15
GRID_SIZE = 600

class AndersonSimulation:
    def __init__(self, n_particles):
        self.n = n_particles
        self.pos = np.zeros((n_particles, 3), dtype=np.float32)
        # Randomly sample particles with exponential falloff from center
        # Inverse transform sampling: r = -loc_len * ln(1 - u)
        loc_len = 120.0
        u = np.random.rand(n_particles).astype(np.float32)
        r = -loc_len * np.log(1.0 - u * 0.999) # Avoid log(0)
        
        # Random directions
        theta = np.random.uniform(0, np.pi, n_particles).astype(np.float32)
        phi = np.random.uniform(0, 2 * np.pi, n_particles).astype(np.float32)
        
        self.pos[:, 0] = r * np.sin(theta) * np.cos(phi)
        self.pos[:, 1] = r * np.sin(theta) * np.sin(phi)
        self.pos[:, 2] = r * np.cos(theta)
        
        self.phase = np.random.rand(n_particles).astype(np.float32) * np.pi * 2
        self.freq = np.random.uniform(0.5, 2.0, n_particles).astype(np.float32)

        # Disordered Grid
        self.grid_nodes = np.stack(np.meshgrid(
            np.linspace(-GRID_SIZE/2, GRID_SIZE/2, GRID_RES),
            np.linspace(-GRID_SIZE/2, GRID_SIZE/2, GRID_RES),
            np.linspace(-GRID_SIZE/2, GRID_SIZE/2, GRID_RES)
        ), axis=-1).reshape(-1, 3).astype(np.float32)
        # Add disorder
        self.grid_nodes += np.random.normal(0, 25, self.grid_nodes.shape).astype(np.float32)

    def get_points(self, t):
        # Breathing / Pulsing
        r_mod = 1.0 + 0.05 * np.sin(t * 0.1 + self.phase)
        p = self.pos * r_mod[:, np.newaxis]
        return p

sim = AndersonSimulation(NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0, 5, 15)

def draw():
    t = py5.frame_count
    py5.background(0, 5, 15)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.003)
    py5.rotate_z(t * 0.001)
    
    # Draw Disordered Grid (Subtle)
    py5.stroke(200, 200, 255, 15)
    py5.stroke_weight(0.5)
    # Draw some grid lines
    # To be fast, we'll only draw a subset of lines
    # Let's just draw nodes as small points
    py5.points(sim.grid_nodes)
    
    # Draw Localized Wavefunction
    points = sim.get_points(t)
    
    # Color mapping: Distance from center
    dist = np.linalg.norm(points, axis=1)
    # Closer = Brighter Cyan, Further = Fainter Amethyst
    
    py5.stroke_weight(1.0)
    for i in range(8):
        r_low = i * 60
        r_high = (i + 1) * 60
        mask = (dist >= r_low) & (dist < r_high)
        if np.any(mask):
            hue = 190 + i * 15 # 190 (Cyan) to 310 (Amethyst)
            alpha = 60 * np.exp(-r_low / 150.0)
            py5.color_mode(py5.HSB, 360, 100, 100, 100)
            py5.stroke(hue, 70, 100, alpha)
            py5.points(points[mask])
            py5.color_mode(py5.RGB, 255, 255, 255, 255)

    py5.pop_matrix()

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "28",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
