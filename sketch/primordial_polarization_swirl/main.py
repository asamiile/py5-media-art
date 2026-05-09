import sys
from pathlib import Path
import numpy as np
import py5
import subprocess

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
NUM_PARTICLES = 120000
INITIAL_RADIUS = 350
EXPANSION_RATE = 1.0005
NOISE_SCALE = 0.003
CURL_STRENGTH = 12.0

FPS = 60
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC

class Simulation:
    def __init__(self):
        # Initialize particles on a sphere
        phi = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
        costheta = np.random.uniform(-1, 1, NUM_PARTICLES)
        theta = np.arccos(costheta)
        
        self.pos = np.zeros((NUM_PARTICLES, 3))
        self.pos[:, 0] = INITIAL_RADIUS * np.sin(theta) * np.cos(phi)
        self.pos[:, 1] = INITIAL_RADIUS * np.sin(theta) * np.sin(phi)
        self.pos[:, 2] = INITIAL_RADIUS * np.cos(theta)
        
        # Pre-assign base hue and alpha
        self.base_hues = np.random.choice([210, 280, 45], size=NUM_PARTICLES, p=[0.6, 0.3, 0.1])
        # Higher alpha for visibility
        self.alphas = np.random.uniform(10, 60, NUM_PARTICLES)

        # Starfield
        self.num_stars = 12000
        self.star_pos = np.random.uniform(-1500, 1500, (self.num_stars, 3))
        self.star_brightness = np.random.uniform(50, 100, self.num_stars)

    def update(self, frame_count):
        # Slow cosmic expansion
        self.pos *= EXPANSION_RATE
        
        # Vectorized curl field advection
        p = self.pos * NOISE_SCALE
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        t = frame_count * 0.005
        
        # Complex multi-harmonic scalar field Phi
        grad_x = np.cos(x + t) * np.sin(y * 0.5) + 0.3 * np.cos(x * 1.5 - t * 0.7)
        grad_y = np.cos(y - t) * np.sin(z * 0.5) + 0.3 * np.cos(y * 1.5 + t * 0.4)
        grad_z = np.cos(z + t * 0.5) * np.sin(x * 0.5) + 0.3 * np.cos(z * 1.5 - t * 0.2)
        
        grad = np.stack([grad_x, grad_y, grad_z], axis=1)
        
        # Curl velocity = grad x pos
        vel = np.cross(grad, self.pos)
        self.pos += vel * (CURL_STRENGTH / INITIAL_RADIUS)

sim = None

def setup():
    global sim
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    sim = Simulation()

def draw():
    # Slightly brighter background for depth
    py5.background(280, 70, 4)
    
    # Camera setup
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_x(py5.frame_count * 0.0015)
    
    # Draw Starfield
    py5.stroke_weight(1.5)
    for i in range(0, sim.num_stars, 3000):
        end = min(i + 3000, sim.num_stars)
        py5.stroke(210, 20, 100, 25) # Slightly blue stars
        py5.points(sim.star_pos[i:end])
        
    sim.update(py5.frame_count)
    
    # Multi-pass additive rendering
    py5.blend_mode(py5.ADD)
    
    for hue_target in [210, 280, 45]:
        mask = (sim.base_hues == hue_target)
        if not np.any(mask): continue
        
        subset_pos = sim.pos[mask]
        
        # Pass 1: Vibrant Glow
        py5.stroke(hue_target, 80, 100, 10)
        py5.stroke_weight(6)
        py5.points(subset_pos)
        
        # Pass 2: Sharp Filaments
        py5.stroke(hue_target, 60, 100, 40)
        py5.stroke_weight(1.5)
        py5.points(subset_pos)

    py5.blend_mode(py5.BLEND)
    
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
