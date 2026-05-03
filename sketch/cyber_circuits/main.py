import numpy as np
from pathlib import Path
import subprocess
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 8
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Cyber Palette
CLR_BG = (4, 6, 10)
CLR_LIME = (204, 255, 0)
CLR_BLUE = (0, 180, 255)
CLR_PINK = (255, 20, 147)
CLR_WHITE = (220, 240, 255)

class Packet:
    def __init__(self, path, color):
        self.path = path # List of (x, y) nodes
        self.color = color
        self.pos_idx = 0
        self.t = 0.0
        self.speed = np.random.uniform(0.04, 0.12)
        self.size = np.random.uniform(3, 7)
        self.dead = False
        self.trail = []

    def update(self):
        self.t += self.speed
        if self.t >= 1.0:
            self.t = 0.0
            self.pos_idx += 1
            if self.pos_idx >= len(self.path) - 1:
                self.dead = True
        
        if not self.dead:
            pos = self.get_pos()
            self.trail.append(pos)
            if len(self.trail) > 10:
                self.trail.pop(0)

    def get_pos(self):
        if self.dead: return self.path[-1]
        p1 = self.path[self.pos_idx]
        p2 = self.path[self.pos_idx + 1]
        return (p1[0] + (p2[0]-p1[0])*self.t, p1[1] + (p2[1]-p1[1])*self.t)

class CyberCircuit:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.nodes = {} # (x, y) -> node_id
        self.node_list = [] # node_id -> (x, y)
        self.adj = {} # node_id -> set of node_ids
        self.edges = [] # (n1, n2, clr, weight)
        self.packets = []
        
        self.generate_multiscale_grid()

    def add_node(self, x, y):
        key = (int(x), int(y))
        if key not in self.nodes:
            node_id = len(self.node_list)
            self.nodes[key] = node_id
            self.node_list.append((x, y))
            self.adj[node_id] = set()
            return node_id
        return self.nodes[key]

    def add_edge(self, n1, n2, clr, weight):
        self.adj[n1].add(n2)
        self.adj[n2].add(n1)
        self.edges.append((n1, n2, clr, weight))

    def generate_multiscale_grid(self):
        # Recursive subdivision to create hierarchical nodes
        def subdivide(x, y, w, h, depth):
            # Create nodes at corners
            self.add_node(x, y)
            self.add_node(x + w, y)
            self.add_node(x, y + h)
            self.add_node(x + w, y + h)
            
            if depth < 4 and (np.random.rand() > 0.4 or depth < 2):
                # Subdivide
                mw, mh = w / 2, h / 2
                subdivide(x, y, mw, mh, depth + 1)
                subdivide(x + mw, y, mw, mh, depth + 1)
                subdivide(x, y + mh, mw, mh, depth + 1)
                subdivide(x + mw, y + mh, mw, mh, depth + 1)
                # Connect center lines
                self.add_node(x + mw, y)
                self.add_node(x, y + mh)
                self.add_node(x + w, y + mh)
                self.add_node(x + mw, y + h)
                self.add_node(x + mw, y + mh)

        subdivide(0, 0, self.w, self.h, 0)

    def grow_path(self):
        # Pick a random node that has at least one neighbor potential
        start_idx = np.random.randint(len(self.node_list))
        curr_idx = start_idx
        path = [curr_idx]
        
        clr = CLR_LIME if np.random.rand() > 0.4 else CLR_BLUE
        weight = np.random.uniform(1, 3)
        
        length = np.random.randint(4, 12)
        for _ in range(length):
            x, y = self.node_list[curr_idx]
            # Find neighbors in the node set (Manhattan)
            candidates = []
            for other_idx, (ox, oy) in enumerate(self.node_list):
                if other_idx == curr_idx: continue
                # Check if it's a neighbor on the grid (approx)
                dist = abs(x - ox) + abs(y - oy)
                if dist > 0 and (abs(x - ox) < 2 or abs(y - oy) < 2) and dist < 200:
                    candidates.append(other_idx)
            
            # Prefer unvisited or new connections
            if not candidates: break
            
            # Simple heuristic: pick nearest
            candidates.sort(key=lambda idx: abs(x - self.node_list[idx][0]) + abs(y - self.node_list[idx][1]))
            next_idx = candidates[np.random.randint(min(3, len(candidates)))]
            
            if next_idx not in path:
                self.add_edge(curr_idx, next_idx, clr, weight)
                path.append(next_idx)
                curr_idx = next_idx
            else:
                break
        
        if len(path) > 2 and np.random.rand() > 0.4:
            self.packets.append(Packet([self.node_list[i] for i in path], CLR_PINK))

    def update(self):
        if py5.frame_count < 200:
            for _ in range(4):
                self.grow_path()
        
        for p in self.packets:
            p.update()
        self.packets = [p for p in self.packets if not p.dead]

def setup():
    py5.size(*SIZE)
    global circuit
    circuit = CyberCircuit(py5.width, py5.height)
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True)
    py5.background(*CLR_BG)

def draw():
    # Trails for everything
    py5.fill(*CLR_BG, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    circuit.update()
    
    py5.blend_mode(py5.ADD)
    
    # Draw edges
    for e in circuit.edges:
        n1, n2, clr, weight = e
        p1, p2 = circuit.node_list[n1], circuit.node_list[n2]
        
        # Subtle lines
        py5.stroke(*clr, 80)
        py5.stroke_weight(weight)
        py5.line(p1[0], p1[1], p2[0], p2[1])
        
        # Points at junctions
        if py5.frame_count % 30 == 0:
            py5.no_stroke()
            py5.fill(*clr, 40)
            py5.ellipse(p1[0], p1[1], 4, 4)

    # Draw packets
    for p in circuit.packets:
        pos = p.get_pos()
        
        # Packet trail
        for i, tp in enumerate(p.trail):
            alpha = (i / len(p.trail)) * 100
            py5.fill(*p.color, alpha)
            py5.ellipse(tp[0], tp[1], p.size * (i/len(p.trail)), p.size * (i/len(p.trail)))
            
        # Packet core
        py5.fill(255)
        py5.ellipse(pos[0], pos[1], p.size * 0.7, p.size * 0.7)
        py5.fill(*p.color, 150)
        py5.ellipse(pos[0], pos[1], p.size, p.size)

    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4")
        ], check=True)
        mid_frame = int(TOTAL_FRAMES * 0.85)
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / "preview.png")], check=True)

if __name__ == "__main__":
    py5.run_sketch()
