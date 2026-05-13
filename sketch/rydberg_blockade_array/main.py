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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
GRID_RES = 10
NUM_ATOMS = GRID_RES**3
SPACING = 80.0

class RydbergSimulation:
    def __init__(self, res):
        self.res = res
        self.n = res**3
        self.grid = np.stack(np.meshgrid(
            np.linspace(-(res-1)*SPACING/2, (res-1)*SPACING/2, res),
            np.linspace(-(res-1)*SPACING/2, (res-1)*SPACING/2, res),
            np.linspace(-(res-1)*SPACING/2, (res-1)*SPACING/2, res)
        ), axis=-1).reshape(-1, 3).astype(np.float32)
        
        self.excited = np.zeros(self.n, dtype=np.float32)
        self.blockade_radius = 120.0

    def update(self, t):
        # A wave of potential excitation
        wave = 0.5 + 0.5 * np.sin(self.grid[:, 0] * 0.01 + self.grid[:, 1] * 0.01 - t * 0.1)
        
        # Simple blockade logic:
        # Sort by wave potential and greedily excite if not blocked
        self.excited.fill(0)
        idx = np.argsort(wave)[::-1]
        
        for i in idx:
            if wave[i] < 0.7: continue
            
            # Check if any already excited atom is too close
            pos = self.grid[i]
            if np.any(self.excited > 0):
                excited_pos = self.grid[self.excited > 0]
                dist = np.linalg.norm(excited_pos - pos, axis=1)
                if np.any(dist < self.blockade_radius):
                    continue
            
            self.excited[i] = 1.0

    def get_points(self):
        return self.grid, self.excited

sim = RydbergSimulation(GRID_RES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0, 5, 20)

def draw():
    t = py5.frame_count
    py5.background(0, 5, 20)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.005)
    py5.rotate_z(t * 0.002)
    
    sim.update(t)
    grid, excited = sim.get_points()
    
    # Draw non-excited atoms as faint points
    py5.stroke(255, 255, 255, 30)
    py5.stroke_weight(2)
    py5.points(grid[excited == 0])
    
    # Draw excited atoms as bright glowing spheres
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    for i in np.where(excited > 0)[0]:
        pos = grid[i]
        # Core
        py5.stroke(20, 90, 100, 100) # Neon Orange
        py5.stroke_weight(6)
        py5.point(*pos)
        
        # Blockade Shell (translucent)
        py5.no_fill()
        py5.stroke(20, 80, 100, 10)
        py5.stroke_weight(1)
        py5.push_matrix()
        py5.translate(*pos)
        py5.sphere(sim.blockade_radius * 0.5)
        py5.pop_matrix()
        
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
