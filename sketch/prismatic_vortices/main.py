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
PREVIEW_FRAME = 200 # Allow time for vortices to develop
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
NUM_PARTICLES = 60000

class PrismaticFlow:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # Initialize particles in a flow from left to right
        self.pos = np.random.rand(NUM_PARTICLES, 2).astype(np.float32)
        self.pos[:, 0] *= w
        self.pos[:, 1] *= h
        self.vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
        self.vel[:, 0] = 3.0 # Main flow velocity
        
        # Vortex generators (oscillating obstacles)
        self.num_vortices = 3
        self.v_phases = np.random.rand(self.num_vortices) * np.pi * 2

    def update(self, frame_count):
        t = frame_count * 0.04
        
        # Position of vortices (Kármán-like oscillation)
        v_pos = np.zeros((self.num_vortices, 2), dtype=np.float32)
        for i in range(self.num_vortices):
            v_pos[i, 0] = self.w * 0.25 + i * 50
            v_pos[i, 1] = self.h/2 + np.sin(t + self.v_phases[i]) * self.h * 0.15
            
        acc = np.zeros_like(self.vel)
        acc[:, 0] = 0.2 # Constant downstream push
        
        # Field advection
        for i in range(self.num_vortices):
            diff = self.pos - v_pos[i]
            dist_sq = np.sum(diff**2, axis=1, keepdims=True)
            dist = np.sqrt(dist_sq) + 1e-6
            
            # Strength of vortex
            strength = 150.0 / (dist + 50.0)
            
            # Vortex rotation
            rot = np.empty_like(diff)
            rot[:, 0] = -diff[:, 1]
            rot[:, 1] = diff[:, 0]
            
            # Alternate rotation direction
            dir = 1.0 if i % 2 == 0 else -1.0
            acc += (rot / dist) * strength * dir
            
        self.vel += acc * 0.15
        self.vel *= 0.94 # High friction for silken lines
        self.pos += self.vel
        
        # Boundary wrapping
        self.pos[:, 0] %= self.w
        self.pos[:, 1] %= self.h

flow = None

def setup():
    global flow
    py5.size(*SIZE, py5.P2D)
    py5.background(2, 4, 12) # Deep obsidian void
    flow = PrismaticFlow(py5.width, py5.height)
    
    # High-density starfield
    py5.stroke_weight(1)
    for _ in range(3000):
        alpha = py5.random(50, 180)
        py5.stroke(200, 220, 255, alpha)
        py5.point(py5.random(py5.width), py5.random(py5.height))
    
    py5.blend_mode(py5.ADD)

def draw():
    global flow
    flow.update(py5.frame_count)
    
    # Prismatic Palette: Cyan, Pink, Amber
    palette = [
        (0, 255, 255),   # Electric Cyan
        (255, 0, 255),   # Laser Pink
        (255, 191, 0)    # Golden Amber
    ]
    
    pos = flow.pos
    vel = flow.vel
    speeds = np.sqrt(np.sum(vel**2, axis=1))
    
    # Draw in three passes for the "prismatic" RGB split feel
    chunk = NUM_PARTICLES // 3
    for i in range(3):
        start, end = i * chunk, (i + 1) * chunk
        c = palette[i]
        
        batch_pos = pos[start:end]
        batch_speeds = speeds[start:end]
        
        # Opacity based on speed to emphasize flow lines
        alphas = np.clip(batch_speeds * 12, 5, 45)
        
        # Slight spatial shift for the "prismatic" effect
        shift_x = (i - 1) * 1.5
        
        py5.stroke_weight(1.0)
        for j in range(len(batch_pos)):
            py5.stroke(c[0], c[1], c[2], alphas[j])
            py5.point(batch_pos[j, 0] + shift_x, batch_pos[j, 1])

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

py5.run_sketch()
