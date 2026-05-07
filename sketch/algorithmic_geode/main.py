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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

class QuadNode:
    def __init__(self, x, y, w, h, depth):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.depth = depth
        self.children = []
        self.is_leaf = True
        
        # Determine if we should split based on noise and depth
        noise_val = py5.noise(x * 0.01, y * 0.01, depth * 0.5)
        if depth < 6 and noise_val > 0.4:
            self.split()

    def split(self):
        self.is_leaf = False
        nw = self.w / 2
        nh = self.h / 2
        self.children = [
            QuadNode(self.x, self.y, nw, nh, self.depth + 1),
            QuadNode(self.x + nw, self.y, nw, nh, self.depth + 1),
            QuadNode(self.x, self.y + nh, nw, nh, self.depth + 1),
            QuadNode(self.x + nw, self.y + nh, nw, nh, self.depth + 1)
        ]

    def draw(self, time_val):
        if self.is_leaf:
            # Draw "building" or "circuit"
            s = py5.sin(time_val + self.x + self.y)
            alpha = 100 + (255 - 100) * (s + 1) / 2
            # Choose color based on position/depth
            hue = (self.depth * 35 + time_val * 8) % 255
            py5.stroke(hue, 180, 255, alpha)
            py5.stroke_weight(1.5) # Increased weight
            py5.no_fill()
            py5.rect(self.x, self.y, self.w, self.h)
            
            # Tiny dots for "windows" with glow
            if self.w > 15:
                py5.stroke_weight(2)
                py5.point(self.x + self.w/2, self.y + self.h/2)
        else:
            for child in self.children:
                child.draw(time_val)

roots = []

def setup():
    global roots
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Pre-generate Quadtree roots for 4 sides
    for i in range(4):
        py5.random_seed(100 + i)
        roots.append(QuadNode(0, 0, 400, 400, 0))

def draw():
    global roots
    py5.background(10) # Near black
    
    # Lighting
    py5.ambient_light(50, 50, 50)
    py5.directional_light(200, 200, 200, 0, 1, -1)
    
    # Camera
    t = py5.frame_count / TOTAL_FRAMES
    cam_z = 1000 + (300 - 1000) * t
    py5.camera(200 * py5.sin(py5.frame_count * 0.01), 0, cam_z, 0, 0, 0, 0, 1, 0)
    
    # Draw Starfield (simple points in 3D)
    py5.stroke(255, 100)
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    np.random.seed(42) # Consistent stars
    for _ in range(500):
        py5.vertex(np.random.uniform(-2000, 2000), np.random.uniform(-2000, 2000), np.random.uniform(-2000, 2000))
    py5.end_shape()
    
    # Draw "Geode" Shards
    py5.push_matrix()
    py5.rotate_y(py5.frame_count * 0.005)
    
    # Draw external obsidian shards with edge highlights
    num_shards = 12
    for i in range(num_shards):
        angle = py5.TWO_PI / num_shards * i
        r = 300
        x = r * py5.cos(angle)
        y = r * py5.sin(angle)
        
        py5.push_matrix()
        py5.translate(x, y, 0)
        py5.rotate_x(angle)
        # Main shard body
        py5.stroke(0, 0, 80, 200) # Brighter edge
        py5.stroke_weight(1)
        py5.fill(0, 0, 15, 230)
        py5.box(100, 400, 50)
        # Inner glow leak at shard junctions
        py5.no_stroke()
        py5.fill(160, 200, 255, 30)
        py5.box(110, 410, 10)
        py5.pop_matrix()
        
    # Draw the internal City Core
    py5.hint(py5.DISABLE_DEPTH_TEST) # Inner glow additive feel
    py5.push_matrix()
    py5.rotate_x(py5.PI/2)
    
    # Add a core "atmosphere" glow
    for g in range(3):
        py5.no_stroke()
        py5.fill(160, 150, 255, 20)
        py5.sphere(150 + g * 50)
    
    # Draw Quadtree City on 4 sides
    for i in range(4):
        py5.push_matrix()
        py5.rotate_y(py5.PI/2 * i)
        py5.translate(-200, -200, 100)
        roots[i].draw(py5.frame_count * 0.05)
        py5.pop_matrix()
    
    py5.pop_matrix()
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.pop_matrix()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        mid = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
