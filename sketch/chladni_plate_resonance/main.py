from pathlib import Path
import shutil
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 150000

class ChladniSimulation:
    def __init__(self, w, h, num_particles):
        self.w = w
        self.h = h
        self.num_particles = num_particles
        
        # Position [x, y]
        self.pos = np.random.rand(self.num_particles, 2)
        
        # Velocity
        self.vel = np.zeros((self.num_particles, 2))
        
        # Color initialization
        self.hue = np.random.uniform(35, 55, self.num_particles) # Gold/Amber
        self.sat = np.random.uniform(180, 255, self.num_particles)
        self.bri = np.random.uniform(200, 255, self.num_particles)
        
        # Colors packed into ARGB32
        a = np.full(self.num_particles, 100, dtype=np.uint32)
        r = np.full(self.num_particles, 255, dtype=np.uint32)
        g = np.full(self.num_particles, 200, dtype=np.uint32)
        b = np.full(self.num_particles, 100, dtype=np.uint32)
        self.colors = (a << 24) | (r << 16) | (g << 8) | b
        
    def get_gradient(self, x, y, t):
        # Time-varying parameters
        # n transitions from 2 to 6, m transitions from 3 to 7
        n = 3.0 + 2.0 * np.sin(t * np.pi * 2.0 + 0.0)
        m = 4.0 + 2.0 * np.cos(t * np.pi * 2.0 * 1.5)
        
        px = x * np.pi
        py = y * np.pi
        
        # Z = sin(n*px)*sin(m*py) + sin(m*px)*sin(n*py)
        Z = np.sin(n * px) * np.sin(m * py) + np.sin(m * px) * np.sin(n * py)
        
        # dZ/dx = n*pi*cos(n*px)*sin(m*py) + m*pi*cos(m*px)*sin(n*py)
        dZdx = n * np.pi * np.cos(n * px) * np.sin(m * py) + m * np.pi * np.cos(m * px) * np.sin(n * py)
        
        # dZ/dy = m*pi*sin(n*px)*cos(m*py) + n*pi*sin(m*px)*cos(n*py)
        dZdy = m * np.pi * np.sin(n * px) * np.cos(m * py) + n * np.pi * np.sin(m * px) * np.cos(n * py)
        
        # grad(Z^2) = 2 * Z * grad(Z)
        gx = 2.0 * Z * dZdx
        gy = 2.0 * Z * dZdy
        
        return gx, gy

    def step(self, t):
        # Calculate gradients at particle positions
        gx, gy = self.get_gradient(self.pos[:, 0], self.pos[:, 1], t)
        
        # Force pushes towards nodes (where Z^2 is minimum, so opposite to gradient)
        # Add some noise to prevent clumping to a single point perfectly
        force_x = -gx * 0.002 + (np.random.randn(self.num_particles) * 0.001)
        force_y = -gy * 0.002 + (np.random.randn(self.num_particles) * 0.001)
        
        self.vel[:, 0] = self.vel[:, 0] * 0.9 + force_x
        self.vel[:, 1] = self.vel[:, 1] * 0.9 + force_y
        
        self.pos += self.vel
        
        # Wrap around edges or bounce
        out_of_bounds_x = (self.pos[:, 0] < 0) | (self.pos[:, 0] > 1)
        out_of_bounds_y = (self.pos[:, 1] < 0) | (self.pos[:, 1] > 1)
        
        self.pos[out_of_bounds_x, 0] = np.random.rand(np.sum(out_of_bounds_x))
        self.pos[out_of_bounds_x, 1] = np.random.rand(np.sum(out_of_bounds_x))
        self.pos[out_of_bounds_y, 0] = np.random.rand(np.sum(out_of_bounds_y))
        self.pos[out_of_bounds_y, 1] = np.random.rand(np.sum(out_of_bounds_y))

sim = None

def setup():
    global sim
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(15, 20, 25)
    sim = ChladniSimulation(py5.width, py5.height, NUM_PARTICLES)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)


def draw():
    global sim
    
    # Fade background slightly for motion blur
    py5.no_stroke()
    py5.fill(15, 20, 25, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    sim.step(t)
    
    # Render particles directly using py5.points()
    px = sim.pos[:, 0] * py5.width
    py = sim.pos[:, 1] * py5.height
    points_array = np.column_stack((px, py))
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.5)
    
    # We can draw all points with a single color for performance, 
    # relying on the additive blending to create intensity.
    py5.stroke(45, 200, 255, 100) # Amber color with some transparency
    py5.points(points_array)
    
    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
