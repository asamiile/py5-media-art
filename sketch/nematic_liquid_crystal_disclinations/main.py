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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
PARTICLE_COUNT = 40000
NUM_DEFECTS = 6
DECAY = 0.95

class LiquidCrystalSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = np.random.uniform(-500, 500, (PARTICLE_COUNT, 3)).astype(np.float32)
        self.vels = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.colors = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.lifetimes = np.random.uniform(0.1, 1.0, PARTICLE_COUNT).astype(np.float32)
        
        # Defect centers (moving vortices)
        self.defects = np.random.uniform(-300, 300, (NUM_DEFECTS, 3)).astype(np.float32)
        self.defect_vels = np.random.randn(NUM_DEFECTS, 3).astype(np.float32) * 2.0
        
        # Palette: Pearl, Blue, Amethyst
        self.palette = [
            [220, 230, 255], # Pearl
            [50, 150, 255],  # Blue
            [180, 80, 255]   # Amethyst
        ]
        self.init_colors()

    def init_colors(self):
        r = np.random.random(PARTICLE_COUNT)
        for i in range(3):
            mask = (r >= i/3) & (r < (i+1)/3)
            self.colors[mask] = self.palette[i]

    def update(self, frame):
        # Move defects
        self.defects += self.defect_vels
        # Bound defects
        mask = np.abs(self.defects) > 400
        self.defect_vels[mask] *= -1
        
        # Add a bit of noise to defect motion
        self.defect_vels += np.random.randn(NUM_DEFECTS, 3).astype(np.float32) * 0.1
        
        # Vectorized Field Calculation (Director Field)
        # Director field is influenced by defects (vortices)
        total_field = np.zeros_like(self.particles)
        for d in self.defects:
            diff = self.particles - d
            dist_sq = np.sum(diff**2, axis=1, keepdims=True) + 1000
            # Vortex-like rotation around defect
            cross = np.cross(diff, [0, 1, 0.1])
            total_field += cross / dist_sq * 5000
            
        # Add some global twist/noise
        t = frame * 0.01
        noise_field = np.stack([
            np.sin(self.particles[:, 1]*0.01 + t),
            np.cos(self.particles[:, 0]*0.01 + t),
            np.sin(self.particles[:, 2]*0.01 + t)
        ], axis=1)
        
        target_vel = total_field * 0.7 + noise_field * 2.0
        self.vels = self.vels * 0.9 + target_vel * 0.1
        self.particles += self.vels
        
        # Recycle particles
        dist = np.sum(self.particles**2, axis=1)
        dead_mask = (dist > 800**2) | (np.random.random(PARTICLE_COUNT) < 0.005)
        if np.any(dead_mask):
            self.particles[dead_mask] = np.random.uniform(-100, 100, (np.sum(dead_mask), 3))
            self.vels[dead_mask] = 0

    def project(self, pos, ry, rz):
        cy, sy = np.cos(ry), np.sin(ry)
        x, z = pos[:, 0], pos[:, 2]
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        cz, sz = np.cos(rz), np.sin(rz)
        y = pos[:, 1]
        x2 = x1 * cz - y * sz
        y2 = x1 * sz + y * cz
        fov = 1200
        z_final = z1 + 1800
        scale = fov / (z_final + 1e-6)
        px = x2 * scale + self.w / 2
        py = y2 * scale + self.h / 2
        return np.stack([px, py], axis=1)

    def draw(self, ry, rz):
        pts = self.project(self.particles, ry, rz)
        
        # Draw in chunks by color for speed
        for i in range(3):
            mask = (np.sum(np.abs(self.colors - self.palette[i]), axis=1) < 1)
            p_chunk = pts[mask]
            c = self.palette[i]
            
            py5.stroke(c[0], c[1], c[2], 120)
            py5.stroke_weight(1.5)
            py5.points(p_chunk)
            
            if py5.frame_count % 2 == 0:
                py5.stroke_weight(4)
                py5.stroke(c[0], c[1], c[2], 40)
                py5.points(p_chunk[::4])

sys_obj = None
stars_pos = None

def setup():
    global sys_obj, stars_pos
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = LiquidCrystalSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (500, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.stroke(120, 60)
    py5.stroke_weight(1)
    py5.points(stars_pos)

    ry = py5.frame_count * 0.005
    rz = py5.frame_count * 0.002
    
    sys_obj.update(py5.frame_count)
    sys_obj.draw(ry, rz)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
                        str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
