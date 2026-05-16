from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Simulation Parameters ---
GRID_SIZE = (135, 240)  # (h, w)
PARTICLE_COUNT = 120000
DECAY_RATE = 0.94
SHEAR_THRESHOLD = 0.02

class TidePool:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.u = np.zeros(GRID_SIZE, dtype=np.float32)
        self.v = np.zeros(GRID_SIZE, dtype=np.float32)
        self.glow = np.zeros(GRID_SIZE, dtype=np.float32)
        self.particles = np.random.rand(PARTICLE_COUNT, 2).astype(np.float32)
        self.particles[:, 0] *= w
        self.particles[:, 1] *= h
        self.p_alpha = np.zeros(PARTICLE_COUNT, dtype=np.float32)
        
    def update(self, frame_count):
        t = frame_count * 0.015
        y = np.linspace(0, 4, GRID_SIZE[0])
        x = np.linspace(0, 4, GRID_SIZE[1])
        xx, yy = np.meshgrid(x, y)
        
        # Velocity Field (Surge + Noise)
        surge = np.sin(t * 0.5) * 0.5 + 0.5
        self.u = np.sin(yy + t) * surge + np.cos(xx * 0.5 - t * 0.3) * 0.2
        self.v = np.cos(xx + t * 0.7) * surge + np.sin(yy * 0.8 + t * 0.4) * 0.2
        
        # Calculate Shear Stress: |du/dy| + |dv/dx|
        du_dy, du_dx = np.gradient(self.u)
        dv_dy, dv_dx = np.gradient(self.v)
        shear = np.abs(du_dy) + np.abs(dv_dx)
        
        # Update Glow Buffer
        excitation = np.maximum(0, shear - SHEAR_THRESHOLD) * 10.0
        self.glow = self.glow * DECAY_RATE + excitation
        self.glow = np.clip(self.glow, 0, 1)
        
        # Advect Particles
        px = (self.particles[:, 0] / self.w * (GRID_SIZE[1]-1)).astype(np.int32)
        py = (self.particles[:, 1] / self.h * (GRID_SIZE[0]-1)).astype(np.int32)
        px = np.clip(px, 0, GRID_SIZE[1]-1)
        py = np.clip(py, 0, GRID_SIZE[0]-1)
        
        self.particles[:, 0] += self.u[py, px] * 5.0
        self.particles[:, 1] += self.v[py, px] * 5.0
        
        # Particle Alpha based on local glow
        self.p_alpha = self.glow[py, px]
        
        # Reset out of bounds
        out = (self.particles[:, 0] < 0) | (self.particles[:, 0] >= self.w) | \
              (self.particles[:, 1] < 0) | (self.particles[:, 1] >= self.h)
        num_out = np.sum(out)
        if num_out > 0:
            self.particles[out] = np.random.rand(num_out, 2).astype(np.float32)
            self.particles[out, 0] *= self.w
            self.particles[out, 1] *= self.h

tp = None

def setup():
    global tp
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    tp = TidePool(py5.width, py5.height)

def draw():
    global tp
    # Midnight Teal background
    py5.background(180, 80, 5)
    
    tp.update(py5.frame_count)
    
    py5.blend_mode(py5.ADD)
    
    # Render particles in alpha batches
    for a_bin in range(0, 100, 10):
        mask = (tp.p_alpha * 100 >= a_bin) & (tp.p_alpha * 100 < a_bin + 10)
        if np.any(mask):
            # Emerald (150) to Cyan (190) based on alpha
            h = 150 + (a_bin / 100) * 40
            py5.stroke(h, 80, 90, a_bin * 0.8)
            py5.stroke_weight(1 + a_bin / 50)
            py5.points(tp.particles[mask])
            
    # Optional "foam" at high velocity
    vel_mag = np.sqrt(tp.u**2 + tp.v**2)
    foam_mask = vel_mag > 0.8
    if np.any(foam_mask):
        # We'll just draw a few random points in foam regions
        # For simplicity, we skip foam to maintain performance
        pass

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "12M",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        subprocess.run(["cp", str(SKETCH_DIR / f"{WORK_NAME}.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
