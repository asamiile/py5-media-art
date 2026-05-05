from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Palette
BG_COLOR = (10, 12, 15)
COBALT = (0, 180, 255)
GOLD = (255, 200, 0)
MAGENTA = (255, 0, 180)
STEEL = (40, 45, 50)

class Lattice:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.nodes = []
        self.edges = []
        self.generate()

    def generate(self):
        # Create a jittered grid
        cols, rows = 12, 8
        dx = self.w / (cols - 1)
        dy = self.h / (rows - 1)
        
        grid = {}
        for r in range(rows):
            for c in range(cols):
                x = c * dx + np.random.uniform(-dx*0.3, dx*0.3)
                y = r * dy + np.random.uniform(-dy*0.3, dy*0.3)
                # Keep edges strictly on boundary for clean look
                if c == 0: x = 0
                if c == cols-1: x = self.w
                if r == 0: y = 0
                if r == rows-1: y = self.h
                
                self.nodes.append(np.array([x, y]))
                grid[(c, r)] = len(self.nodes) - 1

        # Connect neighbors
        for r in range(rows):
            for c in range(cols):
                curr = grid[(c, r)]
                if c < cols - 1:
                    self.edges.append((curr, grid[(c + 1, r)]))
                if r < rows - 1:
                    self.edges.append((curr, grid[(c, r + 1)]))
                # Diagonals for complexity
                if c < cols - 1 and r < rows - 1 and np.random.random() > 0.6:
                    self.edges.append((curr, grid[(c + 1, r + 1)]))

        # Assign "capacity" to edges
        self.edge_capacity = np.random.choice([1, 2, 5], size=len(self.edges), p=[0.6, 0.3, 0.1])
        self.edge_phases = np.random.uniform(0, np.pi * 2, size=len(self.edges))

lattice = None

def setup():
    global lattice
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    lattice = Lattice(SIZE[0], SIZE[1])
    py5.background(*BG_COLOR)

def draw():
    # Subtle fade for trails
    py5.fill(*BG_COLOR, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.05
    
    # Draw Grid Foundation (static/dim)
    py5.stroke(*STEEL, 40)
    py5.stroke_weight(1)
    for n1, n2 in lattice.edges:
        p1, p2 = lattice.nodes[n1], lattice.nodes[n2]
        py5.line(p1[0], p1[1], p2[0], p2[1])

    # Draw Active Currents
    for i, (n1, n2) in enumerate(lattice.edges):
        p1, p2 = lattice.nodes[n1], lattice.nodes[n2]
        cap = lattice.edge_capacity[i]
        phase = lattice.edge_phases[i]
        
        # Surge effect
        surge = (np.sin(t + phase) + 1) / 2
        
        if cap == 5: # Trunk Lines (Cobalt)
            weight = 2 + surge * 3
            alpha = 150 + surge * 105
            py5.stroke(*COBALT, alpha)
            py5.stroke_weight(weight)
            py5.line(p1[0], p1[1], p2[0], p2[1])
            # Add glow
            py5.stroke(*COBALT, alpha * 0.3)
            py5.stroke_weight(weight * 3)
            py5.line(p1[0], p1[1], p2[0], p2[1])
            
        elif cap == 2: # Capillaries (Gold)
            weight = 1 + surge * 1.5
            alpha = 100 + surge * 100
            py5.stroke(*GOLD, alpha)
            py5.stroke_weight(weight)
            py5.line(p1[0], p1[1], p2[0], p2[1])
            
        else: # Minor paths (Low alpha Gold)
            if surge > 0.8:
                py5.stroke(*GOLD, 40)
                py5.stroke_weight(0.5)
                py5.line(p1[0], p1[1], p2[0], p2[1])

    # Draw Leakage/Pressure at Nodes
    for i, node in enumerate(lattice.nodes):
        # Only some nodes leak
        if i % 3 == 0:
            leak_phase = i * 0.1
            leak_surge = (np.sin(t * 1.5 + leak_phase) + 1) / 2
            if leak_surge > 0.7:
                size = 4 + leak_surge * 8
                py5.no_stroke()
                py5.fill(*MAGENTA, (leak_surge - 0.7) * 400) # Quick flash
                py5.ellipse(node[0], node[1], size, size)
                # Small core
                py5.fill(255, 200)
                py5.ellipse(node[0], node[1], 2, 2)

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure no other python processes are running for this sketch
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Save preview from middle of the animation
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
