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
PARTICLE_COUNT = 100000

class GWSystem:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # Grid of tracers in 3D
        num_side = int(np.sqrt(PARTICLE_COUNT))
        x = np.linspace(-800, 800, num_side)
        z = np.linspace(-800, 800, num_side)
        X, Z = np.meshgrid(x, z)
        self.base_pos = np.stack([X.flatten(), np.zeros(X.size), Z.flatten()], axis=1).astype(np.float32)
        self.particles = self.base_pos.copy()
        
        # Binary parameters
        self.mass = 50.0
        self.sep_initial = 400.0
        
        # Indigo, Cyan, White
        self.colors = [
            [20, 10, 60],   # Midnight Indigo
            [0, 255, 255],  # Cyan Glow
            [255, 255, 255] # Stark White
        ]

    def update(self, frame):
        t = frame / TOTAL_FRAMES
        # Chirp effect: separation decreases, frequency increases
        # We'll use a simple power-law for the inspiral
        progress = np.power(t, 2.5) # Accelerates towards the end
        sep = self.sep_initial * (1.0 - progress * 0.98)
        omega = 0.05 + progress * 1.5
        phase = frame * omega
        
        # Positions of BHs
        bh1 = np.array([sep * np.cos(phase), 0, sep * np.sin(phase)])
        bh2 = -bh1
        
        # Spacetime distortion (Potential field ripples)
        # We'll displace particles vertically (y) based on gravitational potential waves
        dist1 = np.linalg.norm(self.base_pos - bh1, axis=1)
        dist2 = np.linalg.norm(self.base_pos - bh2, axis=1)
        
        # Quadrupole ripple proxy: A/r * cos(k*r - omega*t + angle)
        wave_k = 0.1
        wave_speed = 10.0
        
        # Phase delay based on distance
        phi1 = wave_k * dist1 - frame * 0.5
        phi2 = wave_k * dist2 - frame * 0.5
        
        # Ripples
        amp = 100.0 / (dist1 + 100) + 100.0 / (dist2 + 100)
        h1 = (100.0 / (dist1 + 10)) * np.cos(phi1)
        h2 = (100.0 / (dist2 + 10)) * np.cos(phi2)
        
        self.particles[:, 1] = h1 + h2
        
        # Add some "spiraling" displacement
        self.particles[:, 0] = self.base_pos[:, 0] + (h1 + h2) * 0.2
        self.particles[:, 2] = self.base_pos[:, 2] + (h1 + h2) * 0.2
        
        # BH cores
        self.bh_pos = np.stack([bh1, bh2], axis=0)

    def project(self, pos, ry, rx):
        # Rotate
        cy, sy = np.cos(ry), np.sin(ry)
        cx, sx = np.cos(rx), np.sin(rx)
        
        x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
        
        # Ry
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        
        # Rx
        y2 = y * cx - z1 * sx
        z2 = y * sx + z1 * cx
        
        fov = 1200
        z_final = z2 + 1500 # Closer
        scale = fov / (z_final + 1e-6)
        
        px = x1 * scale + self.w / 2
        py = y2 * scale + self.h / 2
        return np.stack([px, py], axis=1), scale

    def draw(self, frame):
        ry = 0.5 + np.sin(frame * 0.005) * 0.2
        rx = 0.8
        
        pts, scale = self.project(self.particles, ry, rx)
        
        # Draw background tracers (Subtle Indigo)
        py5.stroke(60, 50, 150, 100)
        py5.stroke_weight(1.2)
        py5.points(pts[::2])
        
        # Draw highlighted ripples
        disp = np.abs(self.particles[:, 1])
        m = disp > 3.0
        if np.any(m):
            pts_high = pts[m]
            disp_high = disp[m]
            
            # Cyan ripples - Core
            py5.stroke(0, 255, 255, 180)
            py5.stroke_weight(2.5)
            py5.points(pts_high[::2])
            
            # Cyan ripples - Bloom
            py5.stroke(0, 255, 255, 60)
            py5.stroke_weight(5.0)
            py5.points(pts_high[::4])
            
            # White crests
            m2 = disp_high > 8.0 # Lower threshold for more drama
            if np.any(m2):
                py5.stroke(255, 255, 255, 255)
                py5.stroke_weight(1.5)
                py5.points(pts_high[m2])

        # Draw BH cores
        bh_pts, _ = self.project(self.bh_pos, ry, rx)
        py5.stroke(255, 255, 255, 255)
        py5.stroke_weight(15 * scale[0])
        py5.points(bh_pts)
        
        # Core Glow
        py5.stroke(0, 255, 255, 180)
        py5.stroke_weight(35 * scale[0])
        py5.points(bh_pts)
        
        # Outer Core Bloom
        py5.stroke(0, 150, 255, 80)
        py5.stroke_weight(60 * scale[0])
        py5.points(bh_pts)

sys_obj = None
stars_pos = None

def setup():
    global sys_obj, stars_pos
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    sys_obj = GWSystem(py5.width, py5.height)
    stars_pos = np.random.uniform(0, [py5.width, py5.height], (1200, 2)).astype(np.float32)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    # Background stars
    py5.stroke(180, 100)
    py5.stroke_weight(1)
    py5.points(stars_pos)

    sys_obj.update(py5.frame_count)
    sys_obj.draw(py5.frame_count)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"),
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        # Capture near merger (near the end)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.90):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
