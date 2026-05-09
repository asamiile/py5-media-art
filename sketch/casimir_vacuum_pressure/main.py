from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation constants
NUM_PARTICLES = 160_000
NUM_STARS = 12_000

class CasimirSimulation:
    def __init__(self):
        self.p_pos = np.random.uniform(-1500, 1500, (NUM_PARTICLES, 3)).astype(np.float32)
        self.p_life = np.random.uniform(0, 1, NUM_PARTICLES).astype(np.float32)
        self.p_decay = np.random.uniform(0.01, 0.05, NUM_PARTICLES).astype(np.float32)
        self.p_freq = np.random.uniform(0.1, 1.0, NUM_PARTICLES).astype(np.float32)
        
        # Stars
        self.s_pos = np.random.uniform(-2000, 2000, (NUM_STARS, 3)).astype(np.float32)
        self.s_bright = np.random.uniform(50, 200, NUM_STARS).astype(np.float32)
        
    def update(self, frame):
        # Update particles
        self.p_life -= self.p_decay
        mask = self.p_life <= 0
        num_respawn = np.sum(mask)
        if num_respawn > 0:
            self.p_pos[mask] = np.random.uniform(-1500, 1500, (num_respawn, 3))
            self.p_life[mask] = 1.0
            self.p_decay[mask] = np.random.uniform(0.01, 0.05, num_respawn)
            self.p_freq[mask] = np.random.uniform(0.1, 1.0, num_respawn)
            
        # Jitter
        self.p_pos += np.random.normal(0, 2, (NUM_PARTICLES, 3))
        
        # Rotate plates
        angle = frame * 0.01
        self.plate_dist = 300 + 100 * np.sin(frame * 0.02)
        
        # Plate boundary suppression
        n = np.array([np.cos(angle), 0, np.sin(angle)])
        proj = np.dot(self.p_pos, n)
        
        in_between = np.abs(proj) < self.plate_dist / 2
        threshold = 0.5 * (400 / self.plate_dist)
        self.p_suppressed = in_between & (self.p_freq < threshold)

sim = CasimirSimulation()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(5, 5, 15)
    
    # Camera
    py5.camera(1200 * np.sin(py5.frame_count * 0.005), -400, 1200 * np.cos(py5.frame_count * 0.005), 
               0, 0, 0, 0, 1, 0)
    
    sim.update(py5.frame_count)
    
    # Draw Stars
    py5.stroke_weight(1)
    py5.stroke(200, 200, 255, 120)
    py5.points(sim.s_pos)
            
    # Draw Plates
    angle = py5.frame_count * 0.01
    py5.push_matrix()
    py5.rotate_y(angle)
    
    d = sim.plate_dist / 2
    for side in [-1, 1]:
        x = side * d
        # Draw plate glow
        py5.stroke(200, 220, 255, 100) # Increased alpha
        py5.stroke_weight(6) # Increased weight
        grid = np.mgrid[-300:301:60, -300:301:60].reshape(2, -1).T
        pts = np.zeros((grid.shape[0], 3))
        pts[:, 0] = x
        pts[:, 1] = grid[:, 0]
        pts[:, 2] = grid[:, 1]
        py5.points(pts)
        
        # Draw plate core
        py5.stroke(255, 255, 255, 255) # Full alpha
        py5.stroke_weight(3) # Increased weight
        py5.points(pts)
    py5.pop_matrix()
    
    # Draw Particles
    py5.stroke_weight(2.0)
    
    stages = [
        (sim.p_life > 0.7, (200, 220, 255)),
        ((sim.p_life <= 0.7) & (sim.p_life > 0.3), (0, 200, 255)),
        (sim.p_life <= 0.3, (150, 50, 255))
    ]
    
    for mask, color in stages:
        m_ns = mask & ~sim.p_suppressed
        if np.any(m_ns):
            for alpha_bin in range(1, 6):
                a_min = (alpha_bin - 1) * 0.2
                a_max = alpha_bin * 0.2
                m_bin = m_ns & (sim.p_life > a_min) & (sim.p_life <= a_max)
                if np.any(m_bin):
                    py5.stroke(*color, alpha_bin * 60) # Increased alpha
                    py5.points(sim.p_pos[m_bin])
                    
        m_s = mask & sim.p_suppressed
        if np.any(m_s):
            for alpha_bin in range(1, 6):
                a_min = (alpha_bin - 1) * 0.2
                a_max = alpha_bin * 0.2
                m_bin = m_s & (sim.p_life > a_min) & (sim.p_life <= a_max)
                if np.any(m_bin):
                    py5.stroke(*color, alpha_bin * 12) # Increased alpha
                    py5.points(sim.p_pos[m_bin])

    if py5.frame_count <= TOTAL_FRAMES:
        py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "32", # Higher CRF to ensure < 100MB
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        sys.exit() # Force exit to prevent extra frames


py5.run_sketch()
