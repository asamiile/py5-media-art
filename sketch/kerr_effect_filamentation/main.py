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
PARTICLE_COUNT = 80000

class KerrSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = np.random.uniform(0, [w, h], (PARTICLE_COUNT, 2)).astype(np.float32)
        self.velocities = np.zeros_like(self.particles)
        
        # Filament centers
        self.centers = np.random.uniform(0.2, 0.8, (12, 2)) * [w, h]
        self.center_vel = np.random.normal(0, 1.5, (12, 2))
        
    def update(self, frame):
        t = frame * 0.01
        
        # Update center positions slowly
        self.centers += self.center_vel * 0.5
        # Bounce centers
        m = (self.centers < 50) | (self.centers > [self.w-50, self.h-50])
        self.center_vel[m] *= -1
        
        # Reset velocities for a fresh field each frame (drift-based)
        self.velocities *= 0.1
        
        # Apply self-focusing towards centers
        for i in range(len(self.centers)):
            diff = self.centers[i] - self.particles
            dist_sq = np.sum(diff**2, axis=1)[:, np.newaxis]
            
            # Kerr effect: force is strong near centers but decays
            width = 100 + 40 * np.sin(t * 2 + i)
            # Use a soft-core potential to avoid infinite speeds
            force = (diff / (dist_sq + 500)) * 5.0
            # Intensity-based focus
            focus = np.exp(-dist_sq / (2 * width**2))
            self.velocities += force * focus * 15
            
        # Add a central "main beam" along the diagonal
        # Distance to line: |(x-x1)*(y2-y1) - (y-y1)*(x2-x1)| / sqrt(...)
        # Simplified: attraction to center + some noise
        main_diff = np.array([self.w/2, self.h/2]) - self.particles
        self.velocities += (main_diff / 1000) * 0.5
        
        # Diffractive noise (scattering)
        self.velocities += np.random.normal(0, 0.4, self.velocities.shape)
        
        self.particles += self.velocities
        self.particles %= [self.w, self.h]

    def draw(self, frame):
        speed = np.linalg.norm(self.velocities, axis=1)
        
        # 1. Background Haze (Deep Emerald) - Increased Alpha
        py5.stroke(0, 80, 40, 40)
        py5.stroke_weight(1.2)
        py5.points(self.particles[::4])
        
        # 2. Neon Lime Filaments
        m = speed > 1.2
        if np.any(m):
            pts = self.particles[m]
            py5.stroke(120, 255, 60, 90)
            py5.stroke_weight(1.8)
            py5.points(pts[::2])
            
            # 3. Prism White Cores
            m2 = speed[m] > 2.5
            if np.any(m2):
                py5.stroke(220, 255, 240, 160)
                py5.stroke_weight(2.5)
                py5.points(pts[m2])

sys_obj = None

def setup():
    global sys_obj
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = KerrSystem(py5.width, py5.height)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    # Peripheral vignette (Deep Green)
    py5.no_fill()
    for i in range(20):
        py5.stroke(0, 20, 10, 5)
        py5.stroke_weight(py5.width * 0.1)
        py5.ellipse(py5.width/2, py5.height/2, py5.width + i*50, py5.height + i*50)

    sys_obj.update(py5.frame_count)
    sys_obj.draw(py5.frame_count)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.6):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
