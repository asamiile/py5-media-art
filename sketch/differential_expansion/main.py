from pathlib import Path
import sys
import numpy as np
import py5
from scipy.spatial import KDTree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes
from lib.animation import frames_dir, save_animation_frame, render_video_and_preview

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = frames_dir(SKETCH_DIR)
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Growth Parameters
MIN_DIST = 6.0
MAX_DIST = 14.0
REPEL_DIST = 20.0
REPEL_FORCE = 0.5
ATTRACTION_FORCE = 0.12
MAX_NODES = 2500

class DifferentialExpansion:
    def __init__(self):
        # Initialize as a small circle in the center
        num_initial = 40
        angles = np.linspace(0, 2 * np.pi, num_initial, endpoint=False)
        radius = 50.0
        self.nodes = np.stack([
            SIZE[0]/2 + radius * np.cos(angles),
            SIZE[1]/2 + radius * np.sin(angles)
        ], axis=1)
        
        # Starfield
        self.num_stars = 1500
        self.stars = np.random.rand(self.num_stars, 3)
        self.stars[:, 0] *= SIZE[0]
        self.stars[:, 1] *= SIZE[1]

    def update(self):
        num_nodes = len(self.nodes)
        
        # 1. KDTree Repulsion (Fast spatial lookup)
        tree = KDTree(self.nodes)
        pairs = list(tree.query_pairs(REPEL_DIST))
        
        forces = np.zeros_like(self.nodes)
        for i, j in pairs:
            diff = self.nodes[i] - self.nodes[j]
            dist_sq = np.sum(diff**2)
            if dist_sq > 0:
                dist = np.sqrt(dist_sq)
                # Repulsion force
                f = (diff / dist) * (REPEL_DIST - dist) * REPEL_FORCE
                forces[i] += f
                forces[j] -= f
                
        # 2. Neighbor Constraints (Attraction to keep loop together)
        prev_idx = np.roll(np.arange(num_nodes), 1)
        next_idx = np.roll(np.arange(num_nodes), -1)
        
        neighbor_forces = (self.nodes[prev_idx] + self.nodes[next_idx]) / 2.0 - self.nodes
        forces += neighbor_forces * ATTRACTION_FORCE
        
        # Apply forces
        self.nodes += forces
        
        # 3. Subdivision (Insertion)
        if num_nodes < MAX_NODES:
            # Check distance between neighbors
            dists = np.linalg.norm(self.nodes - np.roll(self.nodes, -1, axis=0), axis=1)
            too_far = dists > MAX_DIST
            
            if np.any(too_far):
                new_nodes = []
                for i in range(num_nodes):
                    new_nodes.append(self.nodes[i])
                    if too_far[i]:
                        mid = (self.nodes[i] + self.nodes[(i + 1) % num_nodes]) / 2.0
                        new_nodes.append(mid)
                self.nodes = np.array(new_nodes)
            
        # 4. Global centering
        center = np.mean(self.nodes, axis=0)
        self.nodes += (np.array([SIZE[0]/2, SIZE[1]/2]) - center) * 0.02

    def draw(self, frame_count):
        # Deep oceanic night
        py5.background(3, 7, 14)
        
        # Twinkling stars
        py5.stroke_weight(1)
        t = frame_count * 0.06
        for i in range(self.num_stars):
            x, y, mag = self.stars[i]
            twinkle = 130 + 100 * np.sin(t + i)
            py5.stroke(190, 225, 255, twinkle * mag)
            py5.point(x, y)
            
        # Differential Expansion Structure
        py5.no_fill()
        py5.blend_mode(py5.ADD)
        
        # Layer 1: Wide Deep Emerald Glow
        py5.stroke_weight(7.0)
        py5.stroke(15, 80, 70, 25)
        self._draw_path()
        
        # Layer 2: Seafoam Soft Light
        py5.stroke_weight(3.0)
        py5.stroke(70, 190, 150, 70)
        self._draw_path()
        
        # Layer 3: Core Bioluminescent Cyan
        py5.stroke_weight(1.2)
        py5.stroke(90, 255, 255, 180)
        self._draw_path()
        
        # Shimmering highlights
        py5.stroke_weight(2.5)
        py5.stroke(255, 255, 255, 50)
        step = max(1, len(self.nodes) // 150)
        py5.points(self.nodes[::step])
        
        py5.blend_mode(py5.BLEND)

    def _draw_path(self):
        py5.begin_shape()
        for x, y in self.nodes:
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

simulation = DifferentialExpansion()

def setup():
    py5.size(*SIZE)
    # Clear frames dir if it exists
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # Update multiple times for faster growth if needed
    simulation.update()
    simulation.draw(py5.frame_count)
    
    save_animation_frame(FRAMES_DIR)
    
    if py5.frame_count >= TOTAL_FRAMES:
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_filename=PREVIEW_FILENAME
        )
        py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
