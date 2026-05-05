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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

class Shard:
    def __init__(self, points, detached=False):
        self.points = np.array(points)
        self.center = np.mean(self.points, axis=0)
        self.detached = detached
        self.vel = np.random.uniform(-1, 1, 2) * 0.2 if detached else np.zeros(2)
        self.rot = 0
        self.rot_vel = np.random.uniform(-0.01, 0.01) if detached else 0
        self.hue = np.random.uniform(180, 200) # Cyan-ish
        self.life = 1.0

    def update(self):
        if self.detached:
            self.center += self.vel
            self.rot += self.rot_vel
            self.life -= 0.002
            # Slow expansion from center
            self.vel *= 1.01

    def show(self):
        py5.push_matrix()
        py5.translate(self.center[0], self.center[1])
        py5.rotate(self.rot)
        
        # Draw shard relative to its center
        rel_points = self.points - self.center
        
        # Glow edge
        if self.detached:
            py5.stroke(self.hue, 80, 100, self.life * 100)
            py5.stroke_weight(1.5)
        else:
            py5.stroke(self.hue, 50, 40, 50)
            py5.stroke_weight(0.5)
            
        py5.fill(self.hue, 20, 10 if not self.detached else 10 * self.life, 90)
        
        py5.begin_shape()
        for p in rel_points:
            py5.vertex(p[0], p[1])
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

def split_poly(points, p1, p2):
    """Split a convex polygon by a line (p1, p2)."""
    left, right = [], []
    for i in range(len(points)):
        curr = points[i]
        next_p = points[(i + 1) % len(points)]
        
        # Line side test
        d_curr = (p2[0] - p1[0]) * (curr[1] - p1[1]) - (p2[1] - p1[1]) * (curr[0] - p1[0])
        d_next = (p2[0] - p1[0]) * (next_p[1] - p1[1]) - (p2[1] - p1[1]) * (next_p[0] - p1[0])
        
        if d_curr >= 0:
            left.append(curr)
        else:
            right.append(curr)
            
        # Intersection
        if (d_curr > 0 and d_next < 0) or (d_curr < 0 and d_next > 0):
            # Intersection point
            t = d_curr / (d_curr - d_next)
            inter = curr + t * (next_p - curr)
            left.append(inter)
            right.append(inter)
            
    return np.array(left), np.array(right)

shards = []

def setup():
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial Monolith (Large Centered Rectangle)
    w, h = SIZE[0] * 0.4, SIZE[1] * 0.7
    x0, y0 = (SIZE[0]-w)/2, (SIZE[1]-h)/2
    initial_points = np.array([[x0, y0], [x0+w, y0], [x0+w, y0+h], [x0, y0+h]])
    shards.append(Shard(initial_points))
    
    # Initial subdivision
    for _ in range(6):
        subdivide_random()

def subdivide_random():
    global shards
    if not shards: return
    # Pick a non-detached shard to split
    candidates = [i for i, s in enumerate(shards) if not s.detached]
    if not candidates: return
    idx = np.random.choice(candidates)
    s = shards.pop(idx)
    
    # Random splitting line through center
    angle = np.random.uniform(0, np.pi)
    p1 = s.center
    p2 = p1 + np.array([np.cos(angle), np.sin(angle)])
    
    l, r = split_poly(s.points, p1, p2)
    if len(l) > 2: shards.append(Shard(l))
    if len(r) > 2: shards.append(Shard(r))

def draw():
    py5.background(0)
    
    # Slowly break off shards
    if py5.frame_count % 10 == 0:
        subdivide_random()
        
    if py5.frame_count % 30 == 0:
        # Detach a random edge shard
        candidates = [s for s in shards if not s.detached]
        if candidates:
            # Pick one with high x or y distance from center
            dists = [np.linalg.norm(s.center - np.array(SIZE)/2) for s in candidates]
            target = candidates[np.argmax(dists)]
            target.detached = True
            target.vel = (target.center - np.array(SIZE)/2) * 0.005
            target.rot_vel = np.random.uniform(-0.02, 0.02)

    # Render shards
    for s in shards[:]:
        s.update()
        s.show()
        if s.life <= 0:
            shards.remove(s)

    # Save frame etc
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
