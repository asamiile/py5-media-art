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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
PARTICLE_COUNT = 100000

class ZPinchSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        
        # Initial cylinder
        self.y = np.linspace(-600, 600, PARTICLE_COUNT).astype(np.float32)
        self.theta = np.random.uniform(0, 2 * np.pi, PARTICLE_COUNT).astype(np.float32)
        self.r = np.random.uniform(5, 40, PARTICLE_COUNT).astype(np.float32)
        
        self.particles = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.particles[:, 0] = self.r * np.cos(self.theta)
        self.particles[:, 1] = self.y
        self.particles[:, 2] = self.r * np.sin(self.theta)
        
        self.vels = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.palette_idx = np.random.randint(0, 3, PARTICLE_COUNT)
        
        # Magenta, Blue, White
        self.colors = [
            [255, 50, 180],  # Plasma Magenta
            [50, 100, 255],  # Neon Blue
            [255, 255, 255]  # Blinding White
        ]

    def update(self, frame):
        # Instability magnitude increases over time
        t = frame / TOTAL_FRAMES
        instability = np.sin(t * np.pi * 0.5) * 150.0
        
        # Sausage instability (radial modulation)
        sausage = np.sin(self.y * 0.05) * instability * 0.5
        
        # Kink instability (helical displacement)
        kink_x = np.sin(self.y * 0.02 + frame * 0.1) * instability
        kink_z = np.cos(self.y * 0.02 + frame * 0.1) * instability
        
        target_r = self.r + sausage
        self.particles[:, 0] = target_r * np.cos(self.theta + frame * 0.02) + kink_x
        self.particles[:, 2] = target_r * np.sin(self.theta + frame * 0.02) + kink_z
        
        # Add some ejecting plasma
        eject_mask = (np.random.random(PARTICLE_COUNT) < 0.01) & (frame > 60)
        self.vels[eject_mask] += np.random.randn(np.sum(eject_mask), 3) * 5.0
        self.particles[eject_mask] += self.vels[eject_mask]

    def project(self, pos, ry, rz):
        cy, sy = np.cos(ry), np.sin(ry)
        x, z = pos[:, 0], pos[:, 2]
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        cz, sz = np.cos(rz), np.sin(rz)
        y = pos[:, 1]
        x2 = x1 * cz - y * sz
        y2 = x1 * sz + y * cz
        fov = 1000
        z_final = z1 + 1500
        scale = fov / (z_final + 1e-6)
        px = x2 * scale + self.w / 2
        py = y2 * scale + self.h / 2
        return np.stack([px, py], axis=1)

    def draw(self, ry, rz):
        pts = self.project(self.particles, ry, rz)
        
        for i, c in enumerate(self.colors):
            m = (self.palette_idx == i)
            p_chunk = pts[m]
            
            # High-energy glow
            py5.stroke(c[0], c[1], c[2], 50)
            py5.stroke_weight(8)
            py5.points(p_chunk[::5])
            
            py5.stroke(c[0], c[1], c[2], 150)
            py5.stroke_weight(2)
            py5.points(p_chunk)

sys_obj = None
stars_pos = None

def setup():
    global sys_obj, stars_pos
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = ZPinchSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (500, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.stroke(150, 60)
    py5.stroke_weight(1)
    py5.points(stars_pos)

    ry = py5.frame_count * 0.01
    rz = py5.frame_count * 0.003
    
    sys_obj.update(py5.frame_count)
    sys_obj.draw(ry, rz)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
                        str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES * 3 // 4:04d}.png") # Capture during instability peak
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
