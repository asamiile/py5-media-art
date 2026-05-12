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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
PARTICLE_COUNT = 100000

class ConvectionSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = np.random.uniform(0, [w, h], (PARTICLE_COUNT, 2)).astype(np.float32)
        self.velocities = np.zeros_like(self.particles)
        
    def update(self, frame):
        t = frame * 0.02
        strength = 3.5
        
        # Grid-based field
        gw, gh = 80, 45
        x = np.linspace(0, self.w, gw)
        y = np.linspace(0, self.h, gh)
        X, Y = np.meshgrid(x, y)
        
        # Rayleigh-Benard Roll Model
        kx = 4 * np.pi / self.w
        ky = 2 * np.pi / self.h
        
        # Stream function for rolls
        psi = np.sin(kx * X) * np.cos(ky * Y + t)
        # Add hexagonal perturbation
        psi += 0.3 * np.cos(kx * 0.5 * X - t) * np.sin(ky * 1.5 * Y)
        
        vx = np.gradient(psi, axis=0) * 200 * strength
        vy = -np.gradient(psi, axis=1) * 200 * strength
        
        # Advect
        px = (self.particles[:, 0] / self.w * (gw - 1)).astype(np.int32).clip(0, gw - 1)
        py = (self.particles[:, 1] / self.h * (gh - 1)).astype(np.int32).clip(0, gh - 1)
        
        self.velocities[:, 0] = vx[py, px]
        self.velocities[:, 1] = vy[py, px]
        
        # Add jitter
        self.particles += self.velocities + np.random.normal(0, 0.1, self.velocities.shape)
        self.particles %= [self.w, self.h]

    def draw(self, frame):
        speed = np.linalg.norm(self.velocities, axis=1)
        
        # 1. Base Amber Glow
        py5.stroke(100, 40, 0, 30)
        py5.stroke_weight(1.5)
        py5.points(self.particles[::4])
        
        # 2. Molten Plumes
        m = speed > 2.0
        if np.any(m):
            pts = self.particles[m]
            py5.stroke(255, 120, 10, 60)
            py5.stroke_weight(2.0)
            py5.points(pts[::2])
            
            # 3. Solar Highlights
            m2 = speed[m] > 4.5
            if np.any(m2):
                py5.stroke(255, 240, 150, 120)
                py5.stroke_weight(2.5)
                py5.points(pts[m2])

sys_obj = None

def setup():
    global sys_obj
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = ConvectionSystem(py5.width, py5.height)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    # Bottom Heat Source Glow
    py5.no_stroke()
    for i in range(20):
        h = 100 - i * 5
        py5.fill(40, 10, 0, 5)
        py5.rect(0, py5.height - h, py5.width, h)

    sys_obj.update(py5.frame_count)
    sys_obj.draw(py5.frame_count)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.7):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
