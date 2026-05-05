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
NUM_QUARKS = 12
CONFINEMENT_K = 0.005
DAMPING = 0.98
MAX_SPEED = 5.0
STAR_COUNT = 800

class Quark:
    def __init__(self, x, y, color_type):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.random.uniform(-2, 2, 2)
        self.color_type = color_type  # 0: Red, 1: Green, 2: Blue
        
        # Premium palette: Electric Magenta, Cyber Lime, Cobalt Blue
        if color_type == 0:
            self.base_color = (255, 20, 147) # Magenta
        elif color_type == 1:
            self.base_color = (50, 255, 50)  # Lime
        else:
            self.base_color = (0, 191, 255) # Deep Sky Blue

    def update(self):
        self.vel *= DAMPING
        speed = np.linalg.norm(self.vel)
        if speed > MAX_SPEED:
            self.vel = (self.vel / speed) * MAX_SPEED
        self.pos += self.vel
        
        # Soft boundary repulsion
        margin = 200
        if self.pos[0] < margin: self.vel[0] += 0.2
        if self.pos[0] > SIZE[0] - margin: self.vel[0] -= 0.2
        if self.pos[1] < margin: self.vel[1] += 0.2
        if self.pos[1] > SIZE[1] - margin: self.vel[1] -= 0.2

quarks = []
stars = []
trail_buffer = None

def setup():
    global trail_buffer
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Initialize quarks in triplets (baryons)
    for _ in range(NUM_QUARKS // 3):
        cx, cy = np.random.uniform(SIZE[0]*0.2, SIZE[0]*0.8), np.random.uniform(SIZE[1]*0.2, SIZE[1]*0.8)
        for i in range(3):
            qx = cx + np.random.uniform(-50, 50)
            qy = cy + np.random.uniform(-50, 50)
            quarks.append(Quark(qx, qy, i))
            
    # Initialize starfield
    for _ in range(STAR_COUNT):
        stars.append((
            np.random.uniform(0, SIZE[0]),
            np.random.uniform(0, SIZE[1]),
            np.random.uniform(0.5, 2.5), # size
            np.random.uniform(50, 200)   # alpha
        ))
        
    trail_buffer = py5.create_graphics(*SIZE, py5.P2D)
    trail_buffer.begin_draw()
    trail_buffer.background(0)
    trail_buffer.end_draw()
    
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # 1. Update Physics
    for i, q in enumerate(quarks):
        # Confinement force towards all other quarks in the same triplet?
        # Actually, let's just make it a global confinement for simplicity/visuals
        for j, other in enumerate(quarks):
            if i == j: continue
            diff = other.pos - q.pos
            dist = np.linalg.norm(diff)
            if dist > 0:
                # Strong force increases with distance (simplified)
                force_mag = dist * CONFINEMENT_K
                force = (diff / dist) * force_mag
                q.vel += force
                
                # Jitter
                q.vel += np.random.uniform(-0.1, 0.1, 2)
        
        q.update()

    # 2. Draw Background and Starfield
    py5.background(5, 5, 10) # Deep dark blue/charcoal
    
    # Draw Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        # Subtle twinkle
        alpha = s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 50
        py5.fill(255, alpha)
        py5.circle(sx, sy, s_size)

    # 3. Draw Flux Tubes (Edges)
    py5.blend_mode(py5.ADD)
    for i in range(len(quarks)):
        for j in range(i + 1, len(quarks)):
            q1 = quarks[i]
            q2 = quarks[j]
            dist = np.linalg.norm(q1.pos - q2.pos)
            
            # Tension glow
            alpha = py5.remap(dist, 0, 800, 20, 150)
            alpha = np.clip(alpha, 0, 180)
            
            # Color is a mix of the two quarks
            c1 = np.array(q1.base_color)
            c2 = np.array(q2.base_color)
            avg_color = (c1 + c2) / 2
            
            py5.stroke(*avg_color, alpha)
            py5.stroke_weight(py5.remap(dist, 0, 1000, 1, 4))
            py5.line(q1.pos[0], q1.pos[1], q2.pos[0], q2.pos[1])
            
            # Add a highlight at high tension
            if dist > 600:
                py5.stroke(255, 255, 200, alpha * 0.5)
                py5.stroke_weight(0.5)
                py5.line(q1.pos[0], q1.pos[1], q2.pos[0], q2.pos[1])

    # 4. Draw Quarks (Nodes)
    for q in quarks:
        # Glow
        for r in range(5, 0, -1):
            py5.no_stroke()
            py5.fill(*q.base_color, py5.remap(r, 1, 5, 100, 10))
            py5.circle(q.pos[0], q.pos[1], r * 4)
            
        py5.fill(255)
        py5.circle(q.pos[0], q.pos[1], 3)

    py5.blend_mode(py5.BLEND)

    # 5. Capture Frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Encode Video
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Select preview frame (middle of animation)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
