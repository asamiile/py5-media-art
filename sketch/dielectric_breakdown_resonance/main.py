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
DURATION_SEC = 8
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p2.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # Force 4K resolution (3840x2160)

# Simulation Parameters
NUM_BRANCHES = 10
MAX_DEPTH = 12
PARTICLE_COUNT = 30000
DECAY = 0.92

class DischargeSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.branches = []
        self.particles = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.vels = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.palette_idx = np.zeros(PARTICLE_COUNT, dtype=np.int32)
        self.lifetimes = np.zeros(PARTICLE_COUNT, dtype=np.float32)
        self.active_p_idx = 0
        
        self.colors = [
            np.array([255, 245, 220], dtype=np.float32), # White-Gold
            np.array([100, 220, 255], dtype=np.float32), # Electric Cyan
            np.array([180, 100, 255], dtype=np.float32)  # Amethyst
        ]
        
        self.init_branches()

    def init_branches(self):
        for i in range(NUM_BRANCHES):
            self.branches.append({
                'pos': np.array([0, 0, 0], dtype=np.float32),
                'dir': self.random_unit_vec(),
                'active': True,
                'depth': 0
            })

    def random_unit_vec(self):
        phi = np.random.uniform(0, 2 * np.pi)
        costheta = np.random.uniform(-1, 1)
        theta = np.arccos(costheta)
        return np.array([
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta)
        ], dtype=np.float32)

    def update(self):
        new_active = []
        for b in self.branches:
            step_len = np.random.uniform(10, 30)
            noise_dir = self.random_unit_vec()
            b['dir'] = (b['dir'] * 0.8 + noise_dir * 0.2)
            b['dir'] /= (np.linalg.norm(b['dir']) + 1e-6)
            
            old_pos = b['pos'].copy()
            b['pos'] += b['dir'] * step_len
            
            self.spawn_particles(old_pos, b['pos'])
            
            if b['depth'] < MAX_DEPTH and np.random.random() < 0.1:
                new_active.append({
                    'pos': b['pos'].copy(),
                    'dir': self.random_unit_vec(),
                    'active': True,
                    'depth': b['depth'] + 1
                })
            
            if np.linalg.norm(b['pos']) < 600 and np.random.random() > 0.05:
                new_active.append(b)
        
        self.branches = new_active
        if not self.branches and np.random.random() < 0.1:
            self.init_branches()

        self.particles += self.vels
        self.vels *= 0.95
        self.lifetimes *= DECAY
        self.vels += (np.random.randn(PARTICLE_COUNT, 3) * 0.1).astype(np.float32)

    def spawn_particles(self, p1, p2):
        n = 100
        indices = np.arange(self.active_p_idx, self.active_p_idx + n) % PARTICLE_COUNT
        self.active_p_idx = (self.active_p_idx + n) % PARTICLE_COUNT
        
        t = np.random.uniform(0, 1, (n, 1)).astype(np.float32)
        self.particles[indices] = p1 + (p2 - p1) * t
        self.vels[indices] = (np.random.randn(n, 3) * 2.0).astype(np.float32)
        self.lifetimes[indices] = 1.0
        
        r = np.random.random(n)
        self.palette_idx[indices] = np.where(r < 0.2, 0, np.where(r < 0.7, 1, 2))

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
        mask = self.lifetimes > 0.02
        if not np.any(mask): return
        
        p_active = self.particles[mask]
        pal_active = self.palette_idx[mask]
        life_active = self.lifetimes[mask]
        
        proj_pts = self.project(p_active, ry, rz)
        
        for i, base_col in enumerate(self.colors):
            m = (pal_active == i)
            if not np.any(m): continue
            
            pts = proj_pts[m]
            alpha = np.mean(life_active[m]) * 255
            # Subtle glow (adjusted stroke weights for 4K)
            py5.stroke(base_col[0], base_col[1], base_col[2], alpha)
            py5.stroke_weight(4.0)
            py5.points(pts)
            
            if py5.frame_count % 3 == 0:
                py5.stroke_weight(10)
                py5.stroke(base_col[0], base_col[1], base_col[2], alpha * 0.3)
                py5.points(pts[::2])

sys_obj = None
stars_pos = None

import shutil

def setup():
    global sys_obj, stars_pos
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)  # Capping at 1x density prevents Retina-doubling lag on 4K renders
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = DischargeSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (400, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.stroke(150, 60)
    py5.stroke_weight(2)  # Balanced for 4K
    py5.points(stars_pos)

    ry = py5.frame_count * 0.008
    rz = py5.frame_count * 0.004
    sys_obj.update()
    sys_obj.draw(ry, rz)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress logs to prevent command timeouts
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into 4K video...")
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        
        # Mirror output
        subprocess.run(["cp", str(SKETCH_DIR / f"{WORK_NAME}.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

if __name__ == "__main__":
    py5.run_sketch()
