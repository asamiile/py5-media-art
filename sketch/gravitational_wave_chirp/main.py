from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

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
NUM_PARTICLES = 80000

class ChirpSimulation:
    def __init__(self, n_particles):
        self.n = n_particles
        # Space-filling particles
        self.pos = np.random.uniform(-1000, 1000, (n_particles, 3)).astype(np.float32)
        self.orig_pos = self.pos.copy()
        
    def update(self, t):
        # Time to merger: T_merger = 600 frames (10s)
        t_merger = 600
        if t < t_merger:
            tau = (t_merger - t) / t_merger
            # Orbital distance decreases as tau^(1/4)
            r_orb = 300 * np.power(tau, 0.25)
            # Frequency increases as tau^(-3/8)
            theta = -100 * np.power(tau, 0.625)
            
            # Two mass positions
            m1 = np.array([r_orb * np.cos(theta), r_orb * np.sin(theta), 0], dtype=np.float32)
            m2 = -m1
            
            # Gravitational waves (metric perturbation)
            # Amplitude increases as tau^(-1/4)
            amp = 20.0 / np.power(tau + 0.1, 0.25)
            
            # Distort particles based on wave field
            dist_m1 = np.linalg.norm(self.orig_pos - m1, axis=1)
            dist_m2 = np.linalg.norm(self.orig_pos - m2, axis=1)
            
            # Quadrupole radiation pattern (simplified)
            # Ripples radiating from center
            d_center = np.linalg.norm(self.orig_pos, axis=1)
            wave = amp * np.sin(d_center * 0.05 - theta * 2) * np.exp(-d_center * 0.002)
            
            self.pos[:, 0] = self.orig_pos[:, 0] + wave * (self.orig_pos[:, 0] / (d_center + 1))
            self.pos[:, 1] = self.orig_pos[:, 1] + wave * (self.orig_pos[:, 1] / (d_center + 1))
            
            self.m1, self.m2 = m1, m2
            self.merger = False
        else:
            # Post-merger: Ringdown
            t_ring = t - t_merger
            amp = 200.0 * np.exp(-t_ring * 0.05)
            d_center = np.linalg.norm(self.orig_pos, axis=1)
            wave = amp * np.sin(d_center * 0.05 - t_ring * 0.5) * np.exp(-d_center * 0.001)
            
            self.pos[:, 0] = self.orig_pos[:, 0] + wave * (self.orig_pos[:, 0] / (d_center + 1))
            self.pos[:, 1] = self.orig_pos[:, 1] + wave * (self.orig_pos[:, 1] / (d_center + 1))
            
            self.m1 = self.m2 = np.zeros(3, dtype=np.float32)
            self.merger = True

sim = ChirpSimulation(NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 5, 20)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    py5.background(10, 5, 20)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(1.2) # View from an angle
    py5.rotate_z(t * 0.002)
    
    sim.update(t)
    pos = sim.pos
    
    # Color based on wave amplitude and distance
    d_center = np.linalg.norm(sim.orig_pos, axis=1)
    wave_amp = np.linalg.norm(pos - sim.orig_pos, axis=1)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.stroke_weight(1.5)
    
    # Draw field
    # Purple (280) to Gold (50)
    hue = 280 - wave_amp * 2
    alpha = 10 + wave_amp * 2
    
    # For performance, we'll draw in chunks or use subsampling
    # But 150k is usually fine for points
    py5.stroke(280, 70, 100, 40)
    py5.points(pos)
    
    # Highlight waves
    mask = wave_amp > 10
    if np.any(mask):
        py5.stroke(50, 80, 100, 30)
        py5.points(pos[mask])
        
    # Draw masses
    if not sim.merger:
        py5.stroke(0, 0, 100, 100)
        py5.stroke_weight(8)
        py5.point(*sim.m1)
        py5.point(*sim.m2)
    else:
        # Final flash
        py5.stroke(50, 40, 100, 100 * np.exp(-(t-600)*0.1))
        py5.stroke_weight(20)
        py5.point(0, 0, 0)
    
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    py5.pop_matrix()

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "28",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
