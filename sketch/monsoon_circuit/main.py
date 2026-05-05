from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Colors
COLORS = {
    'bg': (12, 12, 14),
    'teal': np.array([0, 255, 204]),
    'violet': np.array([157, 0, 255]),
    'amber': np.array([255, 191, 0]),
    'rose': np.array([224, 17, 95]),
    'white': np.array([255, 255, 255])
}

class Rect:
    def __init__(self, x, y, w, h, depth=0):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.depth = depth
        self.children = []
        self.is_leaf = True

    def subdivide(self, max_depth, min_size):
        if self.depth >= max_depth or self.w < min_size or self.h < min_size:
            return
        
        if np.random.random() > 0.9 and self.depth > 2:
            return

        nw_w = self.w * np.random.uniform(0.3, 0.7)
        nw_h = self.h * np.random.uniform(0.3, 0.7)
        
        self.children = [
            Rect(self.x, self.y, nw_w, nw_h, self.depth + 1),
            Rect(self.x + nw_w, self.y, self.w - nw_w, nw_h, self.depth + 1),
            Rect(self.x, self.y + nw_h, nw_w, self.h - nw_h, self.depth + 1),
            Rect(self.x + nw_w, self.y + nw_h, self.w - nw_w, self.h - nw_h, self.depth + 1)
        ]
        self.is_leaf = False
        for child in self.children:
            child.subdivide(max_depth, min_size)

class Particle:
    def __init__(self, streets, nodes):
        self.streets = streets
        self.nodes = nodes
        self.reset()
        self.hue_type = 'teal' if np.random.random() > 0.4 else 'violet'
        self.speed = np.random.uniform(3, 8)
        self.thickness = np.random.uniform(1, 3)

    def reset(self):
        # Pick a random node to start
        self.current_node_idx = np.random.randint(len(self.nodes))
        self.pos = self.nodes[self.current_node_idx].copy()
        self.target_node_idx = self.get_random_neighbor(self.current_node_idx)
        self.active = True

    def get_random_neighbor(self, node_idx):
        # Find streets connected to this node
        connected = []
        for s in self.streets:
            if s[0] == node_idx:
                connected.append(s[1])
            elif s[1] == node_idx:
                connected.append(s[0])
        if not connected:
            return np.random.randint(len(self.nodes))
        return np.random.choice(connected)

    def update(self):
        target = self.nodes[self.target_node_idx]
        dir = target - self.pos
        dist = np.linalg.norm(dir)
        
        if dist < self.speed:
            self.pos = target.copy()
            self.current_node_idx = self.target_node_idx
            self.target_node_idx = self.get_random_neighbor(self.current_node_idx)
        else:
            self.pos += (dir / dist) * self.speed

state = {}

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(*COLORS['bg'])
    
    # Generate city grid
    root = Rect(0, 0, py5.width, py5.height)
    root.subdivide(max_depth=6, min_size=60)
    
    # Extract unique nodes and streets
    node_map = {} # (x, y) -> index
    nodes = []
    streets = []
    
    def add_node(p):
        p_tuple = (round(p[0], 2), round(p[1], 2))
        if p_tuple not in node_map:
            node_map[p_tuple] = len(nodes)
            nodes.append(np.array(p, dtype=np.float64))
        return node_map[p_tuple]

    def collect(r):
        if r.is_leaf:
            n1 = add_node((r.x, r.y))
            n2 = add_node((r.x + r.w, r.y))
            n3 = add_node((r.x + r.w, r.y + r.h))
            n4 = add_node((r.x, r.y + r.h))
            streets.extend([(n1, n2), (n2, n3), (n3, n4), (n4, n1)])
        else:
            for child in r.children:
                collect(child)
    
    collect(root)
    
    # Filter unique streets
    unique_streets = list(set(tuple(sorted(s)) for s in streets))
    
    state['nodes'] = nodes
    state['streets'] = unique_streets
    state['particles'] = [Particle(unique_streets, nodes) for _ in range(1200)]
    
    # Accumulation buffer for trails
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    state['buffer'] = np.zeros((h, w, 3), dtype=np.float32)
    state['h'], state['w'] = h, w
    
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Update particles and accumulate into buffer
    # We use a decaying buffer to create trails
    state['buffer'] *= 0.92
    
    particles = state['particles']
    buf = state['buffer']
    h, w = state['h'], state['w']
    scale_x = w / py5.width
    scale_y = h / py5.height
    
    for p in particles:
        p.update()
        ix, iy = int(p.pos[0] * scale_x), int(p.pos[1] * scale_y)
        if 0 <= ix < w and 0 <= iy < h:
            color = COLORS[p.hue_type]
            # Additive splash
            buf[iy, ix] += color * 0.8
            # Pooling effect at nodes
            if np.linalg.norm(p.pos - state['nodes'][p.current_node_idx]) < 2:
                 buf[iy, ix] += COLORS['white'] * 0.2

    # Post-process buffer for rendering
    py5.load_np_pixels()
    
    # Chromatic aberration: shift R and B channels slightly
    # Use a larger shift for higher resolution
    shift = int(3 * scale_x)
    
    # Render with background
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:, :, 3] = 255 # Alpha
    
    # R shift left, B shift right
    out[:, :, 0] = np.clip(np.roll(buf[:, :, 0], -shift, axis=1), 0, 255).astype(np.uint8)
    out[:, :, 1] = np.clip(buf[:, :, 1], 0, 255).astype(np.uint8)
    out[:, :, 2] = np.clip(np.roll(buf[:, :, 2], shift, axis=1), 0, 255).astype(np.uint8)
    
    # Blend with background where buffer is dark
    bg = np.array(COLORS['bg'], dtype=np.uint8)
    mask = (buf.sum(axis=2, keepdims=True) < 5)
    out[:, :, :3] = np.where(mask, bg, out[:, :, :3])
    
    py5.np_pixels[:] = out
    py5.update_np_pixels()
    
    # Draw some "building lights" occasionally
    if py5.frame_count == 1:
        state['buildings'] = []
        for _ in range(40):
            bx = np.random.uniform(0, py5.width)
            by = np.random.uniform(0, py5.height)
            bw = np.random.uniform(20, 100)
            bh = np.random.uniform(20, 100)
            state['buildings'].append((bx, by, bw, bh, np.random.choice(['amber', 'rose'])))

    py5.blend_mode(py5.ADD)
    for bx, by, bw, bh, btype in state['buildings']:
        c = COLORS[btype]
        py5.fill(*c, 20)
        py5.no_stroke()
        py5.rect(bx, by, bw, bh)
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
