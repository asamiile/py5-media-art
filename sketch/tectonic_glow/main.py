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

# Constants
NUM_POINTS = 150
MAX_DIST = 180
SPRING_K = 0.05
DAMPING = 0.95
STAR_COUNT = 1000

class PlateNode:
    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=float)
        self.orig_pos = self.pos.copy()
        self.vel = np.random.uniform(-1, 1, 2)
        self.acc = np.zeros(2)
        
    def update(self):
        # Noise-driven drift
        n = py5.noise(self.pos[0] * 0.005, self.pos[1] * 0.005, py5.frame_count * 0.01)
        angle = n * py5.TWO_PI * 2
        self.acc += np.array([np.cos(angle), np.sin(angle)]) * 0.2
        
        self.vel += self.acc
        self.vel *= DAMPING
        self.pos += self.vel
        self.acc *= 0
        
        # Soft boundary
        margin = 100
        if self.pos[0] < margin: self.vel[0] += 0.5
        if self.pos[0] > SIZE[0] - margin: self.vel[0] -= 0.5
        if self.pos[1] < margin: self.vel[1] += 0.5
        if self.pos[1] > SIZE[1] - margin: self.vel[1] -= 0.5

nodes = []
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Initialize nodes in a grid-ish pattern with jitter
    cols = 15
    rows = 10
    for i in range(cols):
        for j in range(rows):
            x = py5.remap(i, 0, cols-1, 100, SIZE[0]-100) + np.random.uniform(-30, 30)
            y = py5.remap(j, 0, rows-1, 100, SIZE[1]-100) + np.random.uniform(-30, 30)
            nodes.append(PlateNode(x, y))
            
    # Starfield
    for _ in range(STAR_COUNT):
        stars.append((
            np.random.uniform(0, SIZE[0]),
            np.random.uniform(0, SIZE[1]),
            np.random.uniform(0.5, 2.0),
            np.random.uniform(50, 180)
        ))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # 1. Update Nodes
    for n in nodes:
        n.update()
        
    # 2. Draw Background
    py5.background(10, 5, 2) # Deep earth sienna/charcoal
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha)
        py5.circle(sx, sy, s_size)
        
    # 3. Render Tectonic Connections
    py5.blend_mode(py5.ADD)
    
    # We find connections between nearby nodes
    # For performance, we could use a spatial grid, but with 150 points O(N^2) is fine for py5
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            dist = np.linalg.norm(n1.pos - n2.pos)
            
            if dist < MAX_DIST:
                # Calculate "Stress" based on distance deviation from original distance?
                # Actually, let's just use distance for simplicity and visual impact
                stress = py5.remap(dist, 0, MAX_DIST, 1, 0)
                if stress < 0.1: continue
                
                # Molten color palette: Amber -> Magenta -> Violet
                if stress > 0.7:
                    # High stress: Molten Gold
                    py5.stroke(255, 200, 50, stress * 200)
                elif stress > 0.4:
                    # Medium: Electric Magenta
                    py5.stroke(255, 50, 200, stress * 150)
                else:
                    # Low: Deep Violet
                    py5.stroke(150, 50, 255, stress * 100)
                    
                py5.stroke_weight(stress * 5)
                
                # Jitter the line to look like a crack
                x1, y1 = n1.pos
                x2, y2 = n2.pos
                
                # Midpoint displacement for "crack" look
                mid_x = (x1 + x2) / 2 + np.random.uniform(-5, 5) * stress
                mid_y = (y1 + y2) / 2 + np.random.uniform(-5, 5) * stress
                
                py5.no_fill()
                py5.begin_shape()
                py5.vertex(x1, y1)
                py5.quadratic_vertex(mid_x, mid_y, x2, y2)
                py5.end_shape()
                
                # Inner hot core for high stress
                if stress > 0.8:
                    py5.stroke(255, 255, 220, stress * 255)
                    py5.stroke_weight(1)
                    py5.line(x1, y1, x2, y2)

    # 4. Node "Hotspots"
    for n in nodes:
        # Subtle glow at each node
        py5.no_stroke()
        py5.fill(255, 50, 0, 20)
        py5.circle(n.pos[0], n.pos[1], 15)
        py5.fill(255, 150, 0, 100)
        py5.circle(n.pos[0], n.pos[1], 4)

    py5.blend_mode(py5.BLEND)

    # 5. Capture Frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.5):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
