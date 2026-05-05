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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
GRID_SIZE = 100
STAR_COUNT = 1000
DIFFUSION = 0.0001
VISCOSITY = 0.00001
DAMPING = 0.99

class Fluid:
    def __init__(self, size):
        self.size = size
        self.density = np.zeros((size, size), dtype=np.float32)
        self.velocity = np.zeros((size, size, 2), dtype=np.float32)
        
    def add_density(self, x, y, amount):
        self.density[y, x] += amount
        
    def add_velocity(self, x, y, vx, vy):
        self.velocity[y, x] += [vx, vy]
        
    def step(self):
        # 1. Diffuse velocity & density (simplified)
        self.density *= DAMPING
        self.velocity *= DAMPING
        
        # 2. Advect (simplified: shift by velocity)
        y, x = np.indices((self.size, self.size))
        vx, vy = self.velocity[..., 0], self.velocity[..., 1]
        
        new_x = np.clip(x - vx, 0, self.size - 1).astype(int)
        new_y = np.clip(y - vy, 0, self.size - 1).astype(int)
        
        self.density = self.density[new_y, new_x]
        self.velocity = self.velocity[new_y, new_x]
        
        # 3. Add noise-driven forces
        noise_v = np.zeros_like(self.velocity)
        t = py5.frame_count * 0.01
        for i in range(self.size):
            for j in range(self.size):
                angle = py5.noise(i * 0.05, j * 0.05, t) * py5.TWO_PI * 2
                noise_v[j, i] = [np.cos(angle) * 0.5, np.sin(angle) * 0.5]
        self.velocity += noise_v

fluid = Fluid(GRID_SIZE)
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # 1. Update Fluid
    # Inject density/velocity at centers
    if py5.frame_count % 30 == 0:
        cx, cy = np.random.randint(20, 80, 2)
        fluid.add_density(cx, cy, 100)
        fluid.add_velocity(cx, cy, np.random.uniform(-5, 5), np.random.uniform(-5, 5))
        
    fluid.step()
    
    # 2. Draw Background
    py5.background(2, 2, 8)
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 3. Draw Fluid Density
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    cell_w = SIZE[0] / GRID_SIZE
    cell_h = SIZE[1] / GRID_SIZE
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            d = fluid.density[j, i]
            if d > 0.1:
                v_mag = np.linalg.norm(fluid.velocity[j, i])
                hue = py5.remap(v_mag, 0, 5, 180, 280) # Cyan to Amethyst
                alpha = np.clip(d * 2, 0, 80)
                py5.fill(hue, 80, 100, alpha)
                py5.rect(i * cell_w, j * cell_h, cell_w, cell_h)
                
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    py5.blend_mode(py5.BLEND)

    # 4. Capture
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.7):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
