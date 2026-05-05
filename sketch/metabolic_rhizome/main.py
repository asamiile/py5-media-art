from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Algorithm Parameters
NUM_NUTRIENTS = 3000
MIN_DIST = 10
MAX_DIST = 90
GROWTH_STEP = 7

class Node:
    def __init__(self, x, y, parent=None):
        self.pos = np.array([x, y], dtype=np.float32)
        self.parent = parent
        self.direction = np.array([0, 0], dtype=np.float32)
        self.count = 0
        self.thickness = 1.8

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(2, 2, 5) # Deep Void
    py5.no_loop()
    
    # Simulation
    nutrients = np.random.rand(NUM_NUTRIENTS, 2) * np.array([py5.width, py5.height])
    # Multiple start roots
    nodes = []
    for _ in range(5):
        nodes.append(Node(py5.random(py5.width), py5.random(py5.height)))
    
    # Run space-colonization simulation
    for i in range(150):
        grow_rhizome(nodes, nutrients)
    
    # Render
    draw_starfield()
    render_rhizome(nodes)
    add_bioluminescent_glow(nodes)
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def grow_rhizome(nodes, nutrients):
    """One step of the space-colonization algorithm (Optimized)."""
    # Reset directions
    for node in nodes:
        node.direction = np.zeros(2, dtype=np.float32)
        node.count = 0
        
    node_positions = np.array([n.pos for n in nodes])
    
    # For each nutrient, find nearest node (vectorized)
    active_indices = np.where(nutrients[:, 0] != -1)[0]
    if len(active_indices) == 0: return
    
    for idx in active_indices:
        n_pos = nutrients[idx]
        dists = np.linalg.norm(node_positions - n_pos, axis=1)
        
        min_idx = np.argmin(dists)
        best_dist = dists[min_idx]
        
        if best_dist < MIN_DIST:
            nutrients[idx] = -1 # Reached
        elif best_dist < MAX_DIST:
            best_node = nodes[min_idx]
            dir = (n_pos - best_node.pos) / best_dist
            best_node.direction += dir
            best_node.count += 1
            
    # Create new nodes
    new_nodes = []
    for node in nodes:
        if node.count > 0:
            avg_dir = node.direction / node.count
            avg_dir /= np.linalg.norm(avg_dir)
            new_pos = node.pos + avg_dir * GROWTH_STEP
            new_node = Node(new_pos[0], new_pos[1], parent=node)
            new_nodes.append(new_node)
            # Increase thickness of parent path
            p = node
            while p:
                p.thickness += 0.05
                p = p.parent
                if p and p.thickness > 8.0: break # Cap thickness
                
    nodes.extend(new_nodes)

def render_rhizome(nodes):
    """Draw the branching network."""
    py5.push_style()
    py5.no_fill()
    for node in nodes:
        if node.parent:
            # Gradient from neural violet to bio-teal based on thickness/depth
            t = py5.remap(node.thickness, 2.0, 8.0, 0, 1)
            col = py5.lerp_color(0x7B68EE, 0x00FFCC, t) # Neural Violet to Bio-Teal
            py5.stroke(col, 200)
            py5.stroke_weight(node.thickness)
            py5.line(node.pos[0], node.pos[1], node.parent.pos[0], node.parent.pos[1])
    py5.pop_style()

def draw_starfield():
    """Subtle starfield for context."""
    py5.push_style()
    for _ in range(3000):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        mag = np.random.power(5) * 255
        py5.stroke(mag, mag, mag * 1.3, mag * 0.8)
        py5.stroke_weight(py5.random(0.5, 1.5))
        py5.point(x, y)
    py5.pop_style()

def add_bioluminescent_glow(nodes):
    """Add glowing nodes at branch junctions."""
    py5.push_style()
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    for node in nodes:
        # Junctions have higher thickness generally or multiple children
        if node.thickness > 4.0:
            alpha = py5.remap(node.thickness, 4.0, 8.0, 20, 80)
            py5.fill(0, 255, 204, alpha) # Bio-Teal
            py5.circle(node.pos[0], node.pos[1], node.thickness * 1.5)
            
            # Core gold highlight
            if node.thickness > 6.0:
                py5.fill(255, 215, 0, alpha * 1.5)
                py5.circle(node.pos[0], node.pos[1], node.thickness * 0.5)
    py5.pop_style()

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()
