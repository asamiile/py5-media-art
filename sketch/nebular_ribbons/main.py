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
PREVIEW_FRAME = 180
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
NUM_RIBBONS = 14
NODES_PER_RIBBON = 150
NUM_STARS = 2500

class NebularRibbon:
    def __init__(self, w, h, idx):
        self.w, self.h = w, h
        self.idx = idx
        # Initialize nodes in a central cluster
        self.nodes = np.full((NODES_PER_RIBBON, 3), [w/2, h/2, 0], dtype=np.float32)
        # Random walk parameters
        self.noise_seed = np.random.rand(3) * 1000
        # Iridescent palette choice
        palettes = [
            (0, 128, 128),   # Electric Teal
            (230, 230, 250), # Soft Lavender
            (64, 224, 208),  # Bright Turquoise
            (255, 0, 127)    # Deep Rose
        ]
        self.color = palettes[idx % 4]

    def update(self, frame_count):
        t = frame_count * 0.008
        # Shift nodes back
        self.nodes[1:] = self.nodes[:-1]
        
        # New head position driven by multi-octave noise
        # We use large scale noise for main path, fine scale for shimmering
        h = self.nodes[0].copy()
        
        ns = self.noise_seed
        nx = py5.os_noise(t + ns[0], self.idx * 0.5) - 0.5
        ny = py5.os_noise(t + ns[1], self.idx * 0.7) - 0.5
        nz = py5.os_noise(t + ns[2], self.idx * 0.9) - 0.5
        
        h[0] += nx * 35
        h[1] += ny * 35
        h[2] += nz * 20
        
        # Keep within bounds with soft attraction to center
        h[0] += (self.w/2 - h[0]) * 0.01
        h[1] += (self.h/2 - h[1]) * 0.01
        
        self.nodes[0] = h

ribbons = []
stars = None

def setup():
    global ribbons, stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    py5.background(2, 4, 10) # Obsidian void
    
    # Static starfield
    stars = np.random.rand(NUM_STARS, 3) # x, y, brightness
    py5.stroke_weight(1)
    for i in range(NUM_STARS):
        alpha = 50 + 205 * stars[i, 2]
        py5.stroke(200, 220, 255, alpha)
        py5.point(stars[i, 0] * py5.width, stars[i, 1] * py5.height)
        
    for i in range(NUM_RIBBONS):
        ribbons.append(NebularRibbon(py5.width, py5.height, i))

def draw():
    # Subtle decay for trails (not too much to keep it clean)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.fill(2, 4, 10, 8) # Low alpha for long trails
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    py5.blend_mode(py5.ADD)
    
    for r in ribbons:
        r.update(py5.frame_count)
        
        # Render as a silken sheet using nodes
        # We draw a series of quads/strips with varying width
        py5.no_fill()
        py5.stroke_weight(1.5)
        
        # Calculate width modulation (shimmering)
        t = py5.frame_count * 0.05
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for i in range(NODES_PER_RIBBON - 1):
            n1 = r.nodes[i]
            n2 = r.nodes[i+1]
            
            # Distance-based alpha decay along the ribbon
            alpha = py5.remap(i, 0, NODES_PER_RIBBON, 80, 0)
            py5.stroke(r.color[0], r.color[1], r.color[2], alpha)
            
            # Width modulation
            w = 15 * np.sin(t + i * 0.1) * (1 - i / NODES_PER_RIBBON)
            
            # Perpendicular vector for the strip (approximate)
            # In 3D we can use the node velocity or just a fixed offset for simplicity
            py5.vertex(n1[0], n1[1] - w, n1[2])
            py5.vertex(n1[0], n1[1] + w, n1[2])
        py5.end_shape()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

py5.run_sketch()
