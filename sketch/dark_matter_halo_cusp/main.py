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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 140000

class DarkMatterSimulation:
    def __init__(self, n_particles):
        self.n = n_particles
        # Initialize in a diffuse sphere
        r = np.random.uniform(0, 800, n_particles).astype(np.float32)
        theta = np.random.uniform(0, np.pi * 2, n_particles).astype(np.float32)
        phi = np.arccos(np.random.uniform(-1, 1, n_particles)).astype(np.float32)
        
        self.pos = np.stack([
            r * np.sin(phi) * np.cos(theta),
            r * np.sin(phi) * np.sin(theta),
            r * np.cos(phi)
        ], axis=-1)
        
        # Small initial velocities (mostly rotational)
        self.vel = np.cross(self.pos, [0, 0, 1]) * 0.001
        self.vel += np.random.normal(0, 0.1, (n_particles, 3))
        
    def update(self, t):
        # Gravitational attraction to center (simplified NFW potential)
        d = np.linalg.norm(self.pos, axis=1, keepdims=True)
        softening = 50.0
        # Force ~ 1 / (d * (d + s))
        accel = -self.pos / (d * (d + softening)**2 + 0.1) * 200.0
        
        # Dynamic collapse: increase gravity over time
        accel *= (1.0 + t * 0.005)
        
        self.vel += accel
        self.pos += self.vel
        
        # Drag to prevent extreme velocities
        self.vel *= 0.99

sim = DarkMatterSimulation(NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(2, 2, 8)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    py5.background(2, 2, 8)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.003)
    py5.rotate_x(t * 0.001)
    
    sim.update(t)
    pos = sim.pos
    
    # Color based on density (distance to center)
    d = np.linalg.norm(pos, axis=1)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.stroke_weight(1.5)
    
    # Indigo (260) to Silver (200, low sat)
    # Dense center = brighter/whiter
    hue = 260 - 60 * np.exp(-d * 0.01)
    sat = 80 * (d / 800.0)
    bright = 100 * np.exp(-d * 0.002)
    alpha = 5 + 20 * np.exp(-d * 0.005)
    
    # Draw in chunks or just all points
    # P3D points are fast
    py5.stroke(260, 60, 100, 40)
    py5.points(pos)
    
    # Cusp highlight
    mask = d < 100
    if np.any(mask):
        py5.stroke(200, 20, 100, 30)
        py5.stroke_weight(1.5)
        py5.points(pos[mask])
        
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
