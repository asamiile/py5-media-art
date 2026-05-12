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

# Lattice Parameters
GRID_SIZE = 40
SPACING = 30

class SpinIceSimulation:
    def __init__(self, size):
        self.size = size
        # Spins on a square lattice edges (horizontal and vertical)
        # 0: left->right or top->bottom, 1: reverse
        self.h_spins = np.random.randint(0, 2, (size, size))
        self.v_spins = np.random.randint(0, 2, (size, size))
        
        # Monopoles at vertices
        self.monopoles = [] # list of (x, y, type) where type is +1 or -1
        
    def update(self, t):
        # Occasionally spawn a monopole pair
        if t % 60 == 0 and len(self.monopoles) < 10:
            rx, ry = np.random.randint(1, self.size-1, 2)
            self.monopoles.append([rx, ry, 1])
            self.monopoles.append([rx, ry, -1])
            
        # Move monopoles
        for m in self.monopoles:
            # Random walk but biased to keep them apart? 
            # Or just random walk that flips spins
            dx, dy = 0, 0
            if np.random.random() < 0.2:
                move = np.random.choice(['up', 'down', 'left', 'right'])
                if move == 'left' and m[0] > 0:
                    self.h_spins[m[1], m[0]-1] = 1 - self.h_spins[m[1], m[0]-1]
                    m[0] -= 1
                elif move == 'right' and m[0] < self.size-1:
                    self.h_spins[m[1], m[0]] = 1 - self.h_spins[m[1], m[0]]
                    m[0] += 1
                elif move == 'up' and m[1] > 0:
                    self.v_spins[m[1]-1, m[0]] = 1 - self.v_spins[m[1]-1, m[0]]
                    m[1] -= 1
                elif move == 'down' and m[1] < self.size-1:
                    self.v_spins[m[1], m[0]] = 1 - self.v_spins[m[1], m[0]]
                    m[1] += 1

sim = SpinIceSimulation(GRID_SIZE)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count
    if t % 60 == 0:
        print(f"Frame {t}")
    
    # Obsidian Blue background
    py5.background(5, 10, 25)
    
    sim.update(t)
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(0.3)
    py5.rotate_z(t * 0.002)
    
    offset = -GRID_SIZE * SPACING / 2
    
    py5.stroke_weight(1.5)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Draw horizontal spins
    h_indices = np.indices((GRID_SIZE, GRID_SIZE-1))
    y_idx = h_indices[0].flatten()
    x_idx = h_indices[1].flatten()
    s = sim.h_spins[y_idx, x_idx]
    
    px = offset + x_idx * SPACING
    py = offset + y_idx * SPACING
    
    h_lines = np.zeros((len(x_idx), 2, 3), dtype=np.float32)
    mask = (s == 0)
    h_lines[mask, 0] = np.stack([px[mask], py[mask], np.zeros_like(px[mask])], axis=-1)
    h_lines[mask, 1] = np.stack([px[mask]+SPACING, py[mask], np.zeros_like(px[mask])], axis=-1)
    h_lines[~mask, 0] = np.stack([px[~mask]+SPACING, py[~mask], np.zeros_like(px[~mask])], axis=-1)
    h_lines[~mask, 1] = np.stack([px[~mask], py[~mask], np.zeros_like(px[~mask])], axis=-1)
    
    py5.stroke(220, 80, 40, 20)
    py5.lines(h_lines.reshape(-1, 6))

    # Draw vertical spins
    v_indices = np.indices((GRID_SIZE-1, GRID_SIZE))
    y_idx = v_indices[0].flatten()
    x_idx = v_indices[1].flatten()
    s = sim.v_spins[y_idx, x_idx]
    
    px = offset + x_idx * SPACING
    py = offset + y_idx * SPACING
    
    v_lines = np.zeros((len(x_idx), 2, 3), dtype=np.float32)
    mask = (s == 0)
    v_lines[mask, 0] = np.stack([px[mask], py[mask], np.zeros_like(px[mask])], axis=-1)
    v_lines[mask, 1] = np.stack([px[mask], py[mask]+SPACING, np.zeros_like(px[mask])], axis=-1)
    v_lines[~mask, 0] = np.stack([px[~mask], py[~mask]+SPACING, np.zeros_like(px[~mask])], axis=-1)
    v_lines[~mask, 1] = np.stack([px[~mask], py[~mask], np.zeros_like(px[~mask])], axis=-1)
    
    py5.stroke(220, 80, 40, 20)
    py5.lines(v_lines.reshape(-1, 6))

    # Draw monopoles
    py5.stroke_weight(8)
    for m in sim.monopoles:
        px = offset + m[0] * SPACING
        py = offset + m[1] * SPACING
        
        if m[2] == 1:
            py5.stroke(80, 90, 100, 80) # Electric Lime
        else:
            py5.stroke(0, 90, 100, 80) # Deep Crimson
        
        py5.point(px, py, 5)
        
        # Glow
        py5.stroke_weight(15)
        if m[2] == 1:
            py5.stroke(80, 70, 100, 20)
        else:
            py5.stroke(0, 70, 100, 20)
        py5.point(px, py, 5)
        py5.stroke_weight(8)

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
