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
PARTICLE_COUNT = 150000

class AGBSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        
        self.particles = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.vels = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.lifetimes = np.zeros(PARTICLE_COUNT, dtype=np.float32)
        self.palette_idx = np.zeros(PARTICLE_COUNT, dtype=np.int32)
        self.active_p_idx = 0
        
        # Rose Quartz, Burnt Orange, Pale Silver
        self.colors = [
            [255, 180, 200], # Rose
            [255, 120, 40],  # Orange
            [200, 210, 220]  # Silver
        ]

    def trigger_pulse(self, frame):
        num_new = 15000
        start_idx = self.active_p_idx % PARTICLE_COUNT
        end_idx = (start_idx + num_new) % PARTICLE_COUNT
        
        # Generate on sphere
        phi = np.random.uniform(0, 2 * np.pi, num_new)
        costheta = np.random.uniform(-1, 1, num_new)
        theta = np.arccos(costheta)
        
        dirs = np.stack([
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta)
        ], axis=1).astype(np.float32)
        
        # Base expansion speed
        speed = 2.0 + np.random.random(num_new) * 1.5
        
        # Add some "convective" variation
        t = frame * 0.1
        variation = np.sin(phi * 3 + t) * 0.5 + 1.0
        speed *= variation
        
        indices = np.arange(start_idx, start_idx + num_new) % PARTICLE_COUNT
        self.particles[indices] = dirs * 20.0
        self.vels[indices] = dirs * speed[:, np.newaxis]
        self.lifetimes[indices] = 1.0
        self.palette_idx[indices] = np.random.randint(0, 3, num_new)
        
        self.active_p_idx += num_new

    def update(self, frame):
        # Pulsation every 3 seconds
        if frame % 180 == 1:
            self.trigger_pulse(frame)
            
        self.particles += self.vels
        self.vels *= 0.998
        self.lifetimes *= 0.997

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
        z_final = z1 + 1800
        scale = fov / (z_final + 1e-6)
        px = x2 * scale + self.w / 2
        py = y2 * scale + self.h / 2
        return np.stack([px, py], axis=1)

    def draw(self, ry, rz):
        mask = self.lifetimes > 0.01
        if not np.any(mask): return
        
        p_active = self.particles[mask]
        pal_active = self.palette_idx[mask]
        life_active = self.lifetimes[mask]
        pts = self.project(p_active, ry, rz)
        
        for i, c in enumerate(self.colors):
            m = (pal_active == i)
            if not np.any(m): continue
            
            p_chunk = pts[m]
            alpha = np.mean(life_active[m]) * 150
            
            # Subtle glow
            py5.stroke(c[0], c[1], c[2], alpha * 0.3)
            py5.stroke_weight(5)
            py5.points(p_chunk[::3])
            
            py5.stroke(c[0], c[1], c[2], alpha)
            py5.stroke_weight(1.0)
            py5.points(p_chunk)

sys_obj = None
stars_pos = None

def setup():
    global sys_obj, stars_pos
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = AGBSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (500, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.stroke(120, 50)
    py5.stroke_weight(1)
    py5.points(stars_pos)

    ry = py5.frame_count * 0.003
    rz = py5.frame_count * 0.001
    
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
