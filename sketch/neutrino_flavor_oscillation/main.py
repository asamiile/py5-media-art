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
NUM_PARTICLES = 120000
V_SPEED = 12.0

class NeutrinoSimulation:
    def __init__(self, n_particles):
        self.n = n_particles
        # Particles travel along Z axis
        self.pos = np.random.normal(0, 50, (n_particles, 3)).astype(np.float32)
        # Random Z start to fill the beam
        self.pos[:, 2] = np.random.uniform(-1000, 1000, n_particles)
        self.phase = np.random.rand(n_particles).astype(np.float32) * np.pi * 2
        
    def update(self, t):
        # Move forward
        self.pos[:, 2] += V_SPEED
        
        # Helical braiding
        # Frequency depends on Z position (oscillation distance)
        theta = self.pos[:, 2] * 0.005 + self.phase
        radius = 100 + 40 * np.sin(self.pos[:, 2] * 0.01)
        self.pos[:, 0] = radius * np.cos(theta)
        self.pos[:, 1] = radius * np.sin(theta)
        
        # Wrap Z
        mask = self.pos[:, 2] > 1000
        self.pos[mask, 2] -= 2000

    def get_probabilities(self, z):
        # Neutrino oscillation (simplified 3-flavor)
        # P = sin^2(1.27 * delta_m^2 * L / E)
        # We'll use periodic functions to represent the three flavors
        l = z + 1000
        f1 = 0.5 + 0.5 * np.cos(l * 0.003) # Electron
        f2 = 0.5 + 0.5 * np.cos(l * 0.003 + 2*np.pi/3) # Muon
        f3 = 0.5 + 0.5 * np.cos(l * 0.003 + 4*np.pi/3) # Tau
        
        norm = f1 + f2 + f3
        return f1/norm, f2/norm, f3/norm

sim = NeutrinoSimulation(NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 15)

def draw():
    t = py5.frame_count
    py5.background(5, 5, 15)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(0.5 * np.sin(t * 0.01)) # Slight sway
    py5.rotate_x(0.2)
    
    sim.update(t)
    pos = sim.pos
    p1, p2, p3 = sim.get_probabilities(pos[:, 2])
    
    py5.stroke_weight(1.0)
    
    # Additive blending simulation: Sort by Z for better transparency
    # But for 120k particles, we'll just draw them
    
    # Electron: Cyan (180)
    # Muon: Magenta (300)
    # Tau: Gold (50)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Sub-sampling for performance and layered look
    # We'll draw 3 passes
    
    # Cyan pass
    py5.stroke(180, 60, 100, 15)
    mask = p1 > 0.4
    py5.points(pos[mask])
    
    # Magenta pass
    py5.stroke(300, 60, 100, 15)
    mask = p2 > 0.4
    py5.points(pos[mask])
    
    # Gold pass
    py5.stroke(50, 60, 100, 15)
    mask = p3 > 0.4
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
