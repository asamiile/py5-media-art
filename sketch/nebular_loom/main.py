from pathlib import Path
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 180  # Increased to allow for more density
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
NUM_PARTICLES = 50000
NUM_ATTRACTORS = 6

class NebularLoom:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        # Initialize particles in a structured way to encourage "weaving"
        self.pos = np.random.rand(NUM_PARTICLES, 2).astype(np.float32)
        self.pos[:, 0] *= w
        self.pos[:, 1] *= h
        self.vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
        
        # Weaver stars (attractors)
        self.attractors = np.random.rand(NUM_ATTRACTORS, 2).astype(np.float32)
        self.attractor_phases = np.random.rand(NUM_ATTRACTORS) * np.pi * 2
        self.attractor_speeds = 0.005 + np.random.rand(NUM_ATTRACTORS) * 0.015
        self.attractor_radii = np.array([w * 0.3, h * 0.35, w * 0.25, h * 0.4, w * 0.32, h * 0.28])

    def update(self, frame_count):
        t = frame_count * 0.015
        
        # Update weaver stars
        current_attractors = np.zeros_like(self.attractors)
        for i in range(NUM_ATTRACTORS):
            p = self.attractor_phases[i] + t * self.attractor_speeds[i]
            current_attractors[i, 0] = self.w / 2 + np.cos(p * (1.1 + i * 0.1)) * self.attractor_radii[i % 6]
            current_attractors[i, 1] = self.h / 2 + np.sin(p * (0.9 + i * 0.15)) * self.attractor_radii[(i+1) % 6]
            
        # Field advection
        acc = np.zeros_like(self.vel)
        for i in range(NUM_ATTRACTORS):
            diff = current_attractors[i] - self.pos
            dist_sq = np.sum(diff**2, axis=1, keepdims=True)
            dist = np.sqrt(dist_sq) + 1e-6
            
            # Complex force: Attract + Spin + Oscillate
            strength = 80.0 / (dist + 100.0)
            
            # Radial attraction
            acc += (diff / dist) * strength
            
            # Tangential spin (the "weaving" motion)
            spin_dir = np.empty_like(diff)
            spin_dir[:, 0] = -diff[:, 1]
            spin_dir[:, 1] = diff[:, 0]
            acc += (spin_dir / dist) * strength * 1.8
            
        self.vel += acc * 0.15
        self.vel *= 0.92  # High friction for silken flow
        self.pos += self.vel
        
        # Gentle wrapping
        self.pos[:, 0] %= self.w
        self.pos[:, 1] %= self.h

loom = None

def setup():
    global loom
    py5.size(*SIZE, py5.P2D)
    py5.background(2, 4, 12)  # Deep midnight navy
    loom = NebularLoom(py5.width, py5.height)
    
    # Dense starfield
    py5.stroke_weight(1)
    for _ in range(3000):
        # Variation in star color and brightness
        sz = py5.random(1, 2.5)
        py5.stroke_weight(sz)
        if py5.random(1) > 0.9:
            py5.stroke(255, 230, 200, py5.random(100, 200)) # Warm stars
        else:
            py5.stroke(200, 220, 255, py5.random(100, 200)) # Cool stars
        py5.point(py5.random(py5.width), py5.random(py5.height))
    
    py5.blend_mode(py5.ADD)

def draw():
    global loom
    loom.update(py5.frame_count)
    
    # Iridescent Nebula Palette
    # Indigo, Cobalt, Rose Gold, Silver
    palette = [
        (75, 0, 130),   # Electric Indigo
        (0, 100, 255),  # Vivid Cobalt
        (183, 110, 121), # Rose Gold
        (220, 220, 240)  # Shimmering Silver
    ]
    
    # Drawing threads
    # We use multiple passes with slightly different offsets to create a "woven" texture
    pos = loom.pos
    vel = loom.vel
    speeds = np.sqrt(np.sum(vel**2, axis=1))
    
    py5.stroke_weight(1.2)
    
    # Partition particles for coloring
    chunk = NUM_PARTICLES // 4
    for i in range(4):
        start, end = i * chunk, (i + 1) * chunk
        c = palette[i]
        
        # Batch points for performance
        batch_pos = pos[start:end]
        batch_speeds = speeds[start:end]
        
        # Calculate alpha based on speed and frame life
        # Slower particles are dimmer to keep the "flow" lines sharp
        alphas = np.clip(batch_speeds * 15, 10, 40)
        
        # We can't batch stroke() in py5 easily with POINTS, so we use a loop
        # but keep it tight.
        for j in range(len(batch_pos)):
            py5.stroke(c[0], c[1], c[2], alphas[j])
            py5.point(batch_pos[j, 0], batch_pos[j, 1])

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

py5.run_sketch()
