from pathlib import Path
import sys
import py5
import numpy as np

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

# --- Classes ---

class VerletNode:
    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=float)
        self.old_pos = np.array([x, y], dtype=float)
        self.acc = np.zeros(2)
        self.origin = np.array([x, y], dtype=float)

    def update(self):
        vel = (self.pos - self.old_pos) * 0.98  # Damping
        self.old_pos = self.pos.copy()
        self.pos += vel + self.acc
        self.acc *= 0

    def apply_force(self, force):
        self.acc += force

class VerletRing:
    def __init__(self, cx, cy, radius, num_nodes, color):
        self.nodes = []
        for i in range(num_nodes):
            angle = py5.TWO_PI * i / num_nodes
            x = cx + radius * py5.cos(angle)
            y = cy + radius * py5.sin(angle)
            self.nodes.append(VerletNode(x, y))
        self.color = color
        self.radius = radius

    def update(self):
        for node in self.nodes:
            # Spring force back to origin to keep the ring structure
            to_origin = node.origin - node.pos
            node.apply_force(to_origin * 0.05)
            node.update()

        # Constraints between adjacent nodes
        for _ in range(3):  # Multiple iterations for stability
            for i in range(len(self.nodes)):
                n1 = self.nodes[i]
                n2 = self.nodes[(i + 1) % len(self.nodes)]
                
                delta = n1.pos - n2.pos
                dist = np.linalg.norm(delta)
                target_dist = np.linalg.norm(n1.origin - n2.origin)
                
                if dist > 0:
                    diff = (target_dist - dist) / dist
                    offset = delta * diff * 0.5
                    n1.pos += offset
                    n2.pos -= offset

    def display(self):
        py5.no_fill()
        py5.stroke(*self.color)
        py5.stroke_weight(2)
        py5.begin_shape()
        for node in self.nodes:
            py5.curve_vertex(node.pos[0], node.pos[1])
        # Close the loop
        for i in range(3):
            node = self.nodes[i % len(self.nodes)]
            py5.curve_vertex(node.pos[0], node.pos[1])
        py5.end_shape()

class HarmonicEmitter:
    def __init__(self, cx, cy, freq, amp, phase_offset):
        self.pos = np.array([cx, cy])
        self.freq = freq
        self.amp = amp
        self.phase_offset = phase_offset

    def get_displacement(self, target_pos, time):
        dist = np.linalg.norm(target_pos - self.pos)
        # Propagation delay + time-based oscillation
        phase = time * self.freq - dist * 0.02 + self.phase_offset
        mag = py5.sin(phase) * self.amp * (100 / (dist + 10)) # Distance-based decay
        
        dir = target_pos - self.pos
        if np.linalg.norm(dir) > 0:
            dir = dir / np.linalg.norm(dir)
        return dir * mag

# --- Global State ---

rings = []
emitters = []
stars = []
trail_layer = None

def setup():
    global trail_layer
    py5.size(*SIZE, py5.P2D)
    trail_layer = py5.create_graphics(*SIZE, py5.P2D)
    trail_layer.begin_draw()
    trail_layer.background(0, 0) # Transparent
    trail_layer.end_draw()
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    # Initialize Rings
    # Colors: Cyan, Amethyst, Amber, Rose
    palette = [
        (0, 255, 255),   # Cyan
        (153, 50, 204),  # Amethyst
        (255, 191, 0),   # Amber
        (255, 0, 127)    # Rose
    ]
    
    for i in range(4):
        radius = 150 + i * 80
        rings.append(VerletRing(cx, cy, radius, 80, palette[i]))
        
    # Initialize Emitters
    emitters.append(HarmonicEmitter(cx, cy, 0.05, 15, 0))
    emitters.append(HarmonicEmitter(cx - 200, cy + 100, 0.08, 10, py5.PI))
    emitters.append(HarmonicEmitter(cx + 250, cy - 150, 0.06, 12, py5.PI/2))

    # Initialize Stars
    for _ in range(1200):
        x = py5.random(SIZE[0])
        y = py5.random(SIZE[1])
        s = py5.random(0.5, 2.0)
        b = py5.random(150, 255)
        stars.append({'pos': np.array([x, y]), 'size': s, 'bright': b, 'noise_offset': py5.random(1000)})

def draw():
    # 1. Background
    py5.background(5, 5, 12)
    
    # 2. Starfield (Static background layer)
    py5.no_stroke()
    for star in stars:
        twinkle = py5.noise(star['noise_offset'] + py5.frame_count * 0.02)
        alpha = star['bright'] * twinkle
        py5.fill(255, alpha)
        py5.circle(star['pos'][0], star['pos'][1], star['size'])
        
    # 3. Update Physics
    time = py5.frame_count
    for ring in rings:
        for node in ring.nodes:
            total_disp = np.zeros(2)
            for emitter in emitters:
                total_disp += emitter.get_displacement(node.pos, time)
            node.apply_force(total_disp * 0.2)
        ring.update()
        
    # 4. Draw Trails to PGraphics
    trail_layer.begin_draw()
    trail_layer.blend_mode(py5.BLEND)
    # Fade existing trails
    trail_layer.no_stroke()
    trail_layer.fill(0, 15) # Fade
    trail_layer.rect(0, 0, SIZE[0], SIZE[1])
    
    trail_layer.blend_mode(py5.ADD)
    for ring in rings:
        r, g, b = ring.color
        trail_layer.no_fill()
        trail_layer.stroke(r, g, b, 60)
        trail_layer.stroke_weight(2)
        trail_layer.begin_shape()
        for node in ring.nodes:
            trail_layer.curve_vertex(node.pos[0], node.pos[1])
        for i in range(3):
            node = ring.nodes[i % len(ring.nodes)]
            trail_layer.curve_vertex(node.pos[0], node.pos[1])
        trail_layer.end_shape()
    trail_layer.end_draw()
    
    # 5. Composite Trails
    py5.blend_mode(py5.BLEND)
    py5.image(trail_layer, 0, 0)
    
    # 6. Draw Sharp Ring Cores
    py5.blend_mode(py5.ADD)
    for ring in rings:
        r, g, b = ring.color
        # Glow
        py5.stroke_weight(4)
        py5.stroke(r, g, b, 100)
        ring.display()
        # Core
        py5.stroke_weight(1.5)
        py5.stroke(r, g, b, 255)
        ring.display()

    # Save Frame
    save_animation_frame(FRAMES_DIR)

    # Post-process after last frame
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_frame=TOTAL_FRAMES // 2,
            preview_filename=PREVIEW_FILENAME
        )

if __name__ == "__main__":
    py5.run_sketch()
