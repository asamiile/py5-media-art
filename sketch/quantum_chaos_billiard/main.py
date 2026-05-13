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
GRID_SIZE = 256
C = 0.5 # wave speed

class QuantumBilliardSimulation:
    def __init__(self, size):
        self.size = size
        self.u = np.zeros((size, size), dtype=np.float32)
        self.u_prev = np.zeros((size, size), dtype=np.float32)
        
        # Stadium mask
        y, x = np.indices((size, size))
        cx, cy = size // 2, size // 2
        r = size // 4
        dist_to_center_line = np.abs(y - cy)
        dist_to_ends = np.minimum(np.sqrt((x - (cx - r))**2 + (y - cy)**2),
                                  np.sqrt((x - (cx + r))**2 + (y - cy)**2))
        
        # Stadium shape: rect + two half circles
        mask_rect = (x >= cx - r) & (x <= cx + r) & (y >= cy - r) & (y <= cy + r)
        mask_circles = dist_to_ends <= r
        self.mask = mask_rect | mask_circles
        
    def update(self, t):
        # Wave equation: u_next = 2*u - u_prev + c^2 * Laplacian(u)
        laplacian = (np.roll(self.u, 1, axis=0) + np.roll(self.u, -1, axis=0) +
                     np.roll(self.u, 1, axis=1) + np.roll(self.u, -1, axis=1) -
                     4 * self.u)
        
        u_next = 2 * self.u - self.u_prev + (C**2) * laplacian
        u_next *= self.mask # Dirichlet BCs
        
        # Drive the wave with a "scar" frequency occasionally
        if t % 120 < 20:
            # Add a local pulse at a specific spot
            phase = t * 0.3
            self.u[self.size//2, self.size//2 + int(60 * np.cos(phase))] += 1.0 * np.sin(phase)
            
        self.u_prev[:] = self.u
        self.u[:] = u_next * 0.99 # Damping

sim = QuantumBilliardSimulation(GRID_SIZE)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    
    # Deep charcoal background
    py5.background(10, 10, 15)
    
    sim.update(t)
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(0.2)
    py5.rotate_z(t * 0.003)
    
    # Render the wavefield as a point cloud with depth
    # Subsample for performance
    indices = np.where(sim.mask)
    y, x = indices
    skip = 2
    y, x = y[::skip], x[::skip]
    vals = sim.u[y, x]
    
    px = (x / GRID_SIZE - 0.5) * 1200
    py = (y / GRID_SIZE - 0.5) * 800
    pz = vals * 300
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Electric Gold (50) for high amplitude, Deep Indigo (260) for low
    # We use abs(vals) for intensity
    mag = np.abs(vals)
    hues = 260 - 210 * np.clip(mag * 5, 0, 1)
    bright = np.clip(mag * 500, 10, 100)
    alpha = np.clip(mag * 200, 5, 60)
    
    # Drawing points is fast in P3D
    # We'll chunk if needed, but 10k points is fine
    pos = np.stack([px, py, pz], axis=-1)
    
    # Group by hue for stroke efficiency? 
    # Or just one color if it's too slow.
    # For now, let's use a single glowy gold for active parts
    py5.stroke_weight(2.5)
    mask_active = mag > 0.005
    if np.any(mask_active):
        py5.stroke(50, 90, 100, 50) # Gold
        py5.points(pos[mask_active])
        
        # Fainter indigo for the rest
        py5.stroke(260, 80, 50, 15)
        py5.points(pos[~mask_active])

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
