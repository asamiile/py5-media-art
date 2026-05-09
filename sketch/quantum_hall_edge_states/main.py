import sys
from pathlib import Path
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes
from lib.animation import frames_dir, render_video_and_preview

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
OUTPUT_FILENAME = f"{WORK_NAME}.mp4"

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()
NUM_PARTICLES = 160000
FPS = 60
DURATION_SEC = 15
TOTAL_FRAMES = FPS * DURATION_SEC

class Simulation:
    def __init__(self):
        # Fill 4K space
        self.bounds = np.array([1700, 960]) 
        self.pos = np.random.uniform([-self.bounds[0], -self.bounds[1], 0], 
                                     [self.bounds[0], self.bounds[1], 0], (NUM_PARTICLES, 3))
        self.vel = np.random.normal(0, 1.8, (NUM_PARTICLES, 3))
        self.vel[:, 2] = 0
        
        # Physics - Magnetic field strength (Controls orbit size)
        self.B = 1.2
        self.q = 1.0
        self.k_wall = 2.8 # Stiffer wall for sharper edge states
        
        self.is_edge = np.zeros(NUM_PARTICLES, dtype=bool)
        
    def update(self):
        # Lorentz force: F = q * (v x B)
        # B is in Z direction, so v x B = [v.y * B, -v.x * B, 0]
        f_lorentz = self.q * np.stack([self.vel[:, 1] * self.B, -self.vel[:, 0] * self.B, np.zeros(NUM_PARTICLES)], axis=1)
        
        # Confinement potential (Harmonic walls)
        dist_x = np.abs(self.pos[:, 0]) - self.bounds[0]
        dist_y = np.abs(self.pos[:, 1]) - self.bounds[1]
        
        f_wall_x = np.where(dist_x > 0, -self.k_wall * dist_x * np.sign(self.pos[:, 0]), 0)
        f_wall_y = np.where(dist_y > 0, -self.k_wall * dist_y * np.sign(self.pos[:, 1]), 0)
        
        acc = f_lorentz + np.stack([f_wall_x, f_wall_y, np.zeros(NUM_PARTICLES)], axis=1)
        
        # Integrate
        self.vel += acc * 0.1
        self.vel *= 0.995 # Maintaining energy
        self.pos += self.vel
        
        # Identify edge states
        self.is_edge = (np.abs(self.pos[:, 0]) > self.bounds[0] - 30) | (np.abs(self.pos[:, 1]) > self.bounds[1] - 30)

sim = None

def setup():
    global sim
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    sim = Simulation()

def draw():
    # Clear with deep indigo trail (Lower alpha for longer trails)
    py5.blend_mode(py5.BLEND)
    py5.fill(225, 95, 1.2, 8) 
    py5.rect(0, 0, py5.width, py5.height)
    
    # 3D view and center
    py5.translate(py5.width / 2, py5.height / 2, 0)
    # Subtle tilt to give depth
    py5.rotate_x(0.2)
    
    sim.update()
    
    # Multi-pass additive rendering
    py5.blend_mode(py5.ADD)
    
    # 1. Bulk (Deep Cobalt)
    bulk_mask = ~sim.is_edge
    if np.any(bulk_mask):
        subset = sim.pos[bulk_mask]
        py5.stroke(215, 85, 60, 5) # Low alpha for silken texture
        py5.stroke_weight(0.9)
        py5.points(subset)
        
    # 2. Edge States (Electric Lime)
    edge_mask = sim.is_edge
    if np.any(edge_mask):
        subset = sim.pos[edge_mask]
        # Outer Glow
        py5.stroke(80, 100, 100, 10)
        py5.stroke_weight(8.0)
        py5.points(subset)
        # Inner Sharp Core
        py5.stroke(80, 30, 100, 40)
        py5.stroke_weight(1.5)
        py5.points(subset)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        render_video_and_preview(
            SKETCH_DIR, FRAMES_DIR,
            fps=FPS, total_frames=TOTAL_FRAMES,
            output_filename=OUTPUT_FILENAME,
            preview_filename=PREVIEW_FILENAME
        )

if __name__ == "__main__":
    py5.run_sketch()
