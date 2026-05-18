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
PREVIEW_FILENAME = f"{WORK_NAME}_p2.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # Force 4K resolution (3840x2160)

# Simulation Parameters
PARTICLE_COUNT = 80000

class SupernovaSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
        phi = np.random.uniform(0, 2 * np.pi, PARTICLE_COUNT)
        costheta = np.random.uniform(-1, 1, PARTICLE_COUNT)
        theta = np.arccos(costheta)
        
        dir_x = np.sin(theta) * np.cos(phi)
        dir_y = np.sin(theta) * np.sin(phi)
        dir_z = np.cos(theta)
        self.dirs = np.stack([dir_x, dir_y, dir_z], axis=1).astype(np.float32)
        
        self.speeds = np.random.exponential(5.0, PARTICLE_COUNT).astype(np.float32) + 1.0
        self.vels = self.dirs * self.speeds[:, np.newaxis]
        
        self.lifetimes = np.ones(PARTICLE_COUNT, dtype=np.float32)
        self.palette_idx = np.random.randint(0, 3, PARTICLE_COUNT)
        
        self.lifetimes[:5000] = 2.0
        self.speeds[:5000] *= 0.2
        self.vels[:5000] = self.dirs[:5000] * self.speeds[:5000, np.newaxis]

        self.colors = [
            [255, 180, 50],  # Deep Gold
            [160, 80, 255],  # Neon Violet
            [255, 255, 255]  # Star-White
        ]

    def update(self, frame):
        self.particles += self.vels
        self.vels *= 0.992
        self.lifetimes *= 0.995
        
        t = frame * 0.03
        noise = np.stack([
            np.sin(self.particles[:, 1] * 0.01 + t) + np.sin(self.particles[:, 2] * 0.02 + t*0.5),
            np.cos(self.particles[:, 0] * 0.01 + t) + np.cos(self.particles[:, 2] * 0.02 + t*0.7),
            np.sin(self.particles[:, 0] * 0.02 + t*0.3) + np.cos(self.particles[:, 1] * 0.01 + t)
        ], axis=1) * 0.8
        self.vels += noise

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
        mask = self.lifetimes > 0.05
        if not np.any(mask): return
        
        p_active = self.particles[mask]
        pal_active = self.palette_idx[mask]
        life_active = self.lifetimes[mask]
        pts = self.project(p_active, ry, rz)
        
        for i, c in enumerate(self.colors):
            m = (pal_active == i)
            if not np.any(m): continue
            
            p_chunk = pts[m]
            # Much brighter alpha
            alpha_base = np.mean(life_active[m]) * 255
            
            # Subtle glow (adjusted stroke weights for 4K)
            # Massive Glow
            py5.stroke(c[0], c[1], c[2], alpha_base * 0.3)
            py5.stroke_weight(24)
            py5.points(p_chunk[::2])
            
            # Mid Glow
            py5.stroke(c[0], c[1], c[2], alpha_base * 0.6)
            py5.stroke_weight(10)
            py5.points(p_chunk)
            
            # Core
            py5.stroke(255, 255, 255, alpha_base)
            py5.stroke_weight(3.0)
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
    sys_obj = SupernovaSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (600, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.stroke(120, 70)
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
