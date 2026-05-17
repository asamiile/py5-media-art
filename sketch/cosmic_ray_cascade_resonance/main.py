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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # Force 4K resolution (3840x2160)

# Simulation Parameters
PARTICLE_COUNT = 50000

class CascadeSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.vels = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        self.palette_idx = np.zeros(PARTICLE_COUNT, dtype=np.int32)
        self.lifetimes = np.zeros(PARTICLE_COUNT, dtype=np.float32)
        self.active_p_idx = 0
        
        self.colors = [
            [255, 250, 240], # White
            [100, 230, 255], # Cyan
            [180, 120, 255]  # Amethyst
        ]
        
        self.reset_shower()

    def reset_shower(self):
        self.active_p_idx = 0
        self.particles.fill(0)
        self.vels.fill(0)
        self.lifetimes.fill(0)
        self.particles[0] = [0, -600, 0]
        self.vels[0] = [0, 20, 0]
        self.lifetimes[0] = 1.0
        self.palette_idx[0] = 0
        self.active_p_idx = 1

    def random_unit_vec(self):
        phi = np.random.uniform(0, 2 * np.pi)
        costheta = np.random.uniform(-1, 1)
        theta = np.arccos(costheta)
        return np.array([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], dtype=np.float32)

    def update(self, frame):
        self.particles += self.vels
        self.lifetimes *= 0.985
        
        active_mask = (self.lifetimes > 0.4) & (self.active_p_idx < PARTICLE_COUNT - 100)
        if np.any(active_mask):
            candidates = np.where(active_mask)[0]
            if len(candidates) > 100:
                candidates = np.random.choice(candidates, 100, replace=False)
                
            for idx in candidates:
                if np.random.random() < 0.2:
                    num_new = np.random.randint(2, 6)
                    for _ in range(num_new):
                        new_idx = self.active_p_idx % PARTICLE_COUNT
                        self.particles[new_idx] = self.particles[idx].copy()
                        v = self.vels[idx].copy()
                        v += np.random.randn(3) * 3.0
                        v[1] = np.abs(v[1]) + 3.0
                        self.vels[new_idx] = v
                        self.lifetimes[new_idx] = self.lifetimes[idx] * 0.98
                        self.palette_idx[new_idx] = np.random.randint(0, 3)
                        self.active_p_idx += 1
                    self.lifetimes[idx] *= 0.7
                    
        if frame % 80 == 0:
            self.reset_shower()

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
            alpha = np.mean(life_active[m]) * 255
            
            # Subtle glow (adjusted stroke weights for 4K)
            py5.stroke(c[0], c[1], c[2], alpha * 0.5)
            py5.stroke_weight(12)
            py5.points(p_chunk)
            
            py5.stroke(255, 255, 255, alpha)
            py5.stroke_weight(4.0)
            py5.points(p_chunk)

sys_obj = None
stars_pos = None

import shutil

def setup():
    global sys_obj, stars_pos
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)  # Capping at 1x density prevents Retina-doubling lag on 4K renders
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = CascadeSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (500, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.stroke(120, 80)
    py5.stroke_weight(2)  # Balanced for 4K
    py5.points(stars_pos)

    ry = py5.frame_count * 0.005
    rz = py5.frame_count * 0.002
    
    sys_obj.update(py5.frame_count)
    sys_obj.draw(ry, rz)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress logs to prevent command timeouts
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into 4K video...")
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
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
