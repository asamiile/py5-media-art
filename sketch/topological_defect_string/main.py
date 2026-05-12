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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
GRID_SIZE = 256
NUM_PARTICLES = 100000

class CosmicStringSimulation:
    def __init__(self, size):
        self.size = size
        # Complex scalar field
        self.phi = (np.random.normal(0, 0.5, (size, size)) + 
                    1j * np.random.normal(0, 0.5, (size, size))).astype(np.complex64)
        
    def update(self, t):
        # Time-dependent Ginzburg-Landau-ish evolution
        # Phase transition: potential changes from parabolic to Mexican hat
        # t=0: parabolic, t=TOTAL_FRAMES: deep Mexican hat
        transition = min(1.0, t / (TOTAL_FRAMES * 0.4))
        
        # Laplacian (periodic BCs)
        laplacian = (np.roll(self.phi, 1, axis=0) + np.roll(self.phi, -1, axis=0) +
                     np.roll(self.phi, 1, axis=1) + np.roll(self.phi, -1, axis=1) -
                     4 * self.phi)
        
        # d_phi/dt = Laplacian - dV/d_phi
        # V = -alpha*|phi|^2 + beta*|phi|^4
        alpha = -1.0 + 2.0 * transition
        beta = 1.0
        
        dV_dphi = self.phi * (alpha + beta * np.abs(self.phi)**2)
        
        dt = 0.05
        self.phi += (laplacian - dV_dphi) * dt
        
        # Add a bit of noise to prevent stagnation
        if transition < 0.8:
            self.phi += (np.random.normal(0, 0.01, (self.size, self.size)) + 
                         1j * np.random.normal(0, 0.01, (self.size, self.size)))

    def get_string_particles(self, n_particles):
        # Strings are where |phi| is minimal (defect cores)
        mag = np.abs(self.phi)
        # Find points with low magnitude
        # We'll sample and keep those with low |phi|
        indices = np.random.randint(0, self.size, (n_particles, 2))
        mvals = mag[indices[:, 0], indices[:, 1]]
        
        # Threshold for core
        mask = mvals < 0.2
        p_indices = indices[mask]
        
        # Map to world coords
        x = (p_indices[:, 1] / self.size - 0.5) * 1600
        y = (p_indices[:, 0] / self.size - 0.5) * 1600
        z = np.random.normal(0, 50, len(x))
        
        return np.stack([x, y, z], axis=-1), mvals[mask]

sim = CosmicStringSimulation(GRID_SIZE)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 8, 5)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    py5.background(10, 8, 5)
    
    sim.update(t)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(0.5)
    py5.rotate_z(t * 0.005)
    
    # Draw background field (subsampled grid)
    # Using field phase for color
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Draw cosmic strings
    pos, mvals = sim.get_string_particles(NUM_PARTICLES)
    
    # Primordial Gold (50) to Cobalt (210)
    # Background: Gold, Strings: Cobalt
    
    # Field background - only draw occasionally or subsampled
    if t % 2 == 0:
        indices = np.random.randint(0, GRID_SIZE, (50000, 2))
        px = (indices[:, 1] / GRID_SIZE - 0.5) * 1800
        py = (indices[:, 0] / GRID_SIZE - 0.5) * 1800
        pz = np.random.uniform(-200, -50, 50000)
        
        phases = np.angle(sim.phi[indices[:, 0], indices[:, 1]])
        hues = 45 + (phases / np.pi) * 15 # Gold range
        
        # Vectorized points for speed
        py5.stroke_weight(2.0)
        # We'll map phases to hues then use stroke and points
        # Actually py5.points doesn't take colors per point directly without vertex
        # But we can chunk by hue if needed, or just use one gold hue for the whole background for now
        # to keep it fast, or a few bands
        
        # Simplest: one gold hue with alpha variations
        py5.stroke(45, 90, 100, 30)
        fpos = np.stack([px, py, pz], axis=-1)
        py5.points(fpos)

    # Strings
    if len(pos) > 0:
        py5.stroke_weight(2.0)
        # Cobalt cores
        py5.stroke(210, 90, 100, 40)
        py5.points(pos)
        
        # Glow
        py5.stroke_weight(4.0)
        py5.stroke(210, 70, 100, 10)
        py5.points(pos)

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
