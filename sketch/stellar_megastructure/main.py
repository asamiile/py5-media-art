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
SHELL_RADIUS = 300
CORE_RADIUS = 120
STAR_COUNT = 3000
MAX_DEPTH = 6
SUBDIVIDE_THRESHOLD = 0.45

# Palette
CORE_GOLD = (255, 215, 0)
OBSIDIAN = (5, 5, 5)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

class ShellQuad:
    def __init__(self, t0, t1, p0, p1, depth):
        self.t0, self.t1 = t0, t1
        self.p0, self.p1 = p0, p1
        self.depth = depth
        self.children = []
        
        mid_t = (t0 + t1) / 2
        mid_p = (p0 + p1) / 2
        
        # Subdivide based on noise
        n = py5.noise(mid_t * 2.0, mid_p * 2.0, depth * 0.5)
        if depth < MAX_DEPTH and n > SUBDIVIDE_THRESHOLD:
            self.children = [
                ShellQuad(t0, mid_t, p0, mid_p, depth + 1),
                ShellQuad(mid_t, t1, p0, mid_p, depth + 1),
                ShellQuad(t0, mid_t, mid_p, p1, depth + 1),
                ShellQuad(mid_t, t1, mid_p, p1, depth + 1),
            ]

    def render(self, time_val, core_pulse):
        if self.children:
            for child in self.children:
                child.render(time_val, core_pulse)
        else:
            mid_t = (self.t0 + self.t1) / 2
            mid_p = (self.p0 + self.p1) / 2
            
            # Oscillate slab height and position slightly
            n_height = py5.noise(mid_t * 5.0, mid_p * 5.0, time_val * 0.5)
            h = 10 + n_height * 40
            
            py5.push_matrix()
            py5.rotate_y(mid_p)
            py5.rotate_z(mid_t)
            py5.translate(SHELL_RADIUS + h/2, 0, 0)
            
            # Render slab
            py5.stroke(40)
            py5.fill(*OBSIDIAN)
            box_w = (self.p1 - self.p0) * SHELL_RADIUS * py5.sin(mid_t) * 0.95
            box_h = (self.t1 - self.t0) * SHELL_RADIUS * 0.95
            py5.box(h, box_h, box_w)
            
            # Render neon conduits on top
            if n_height > 0.7:
                py5.push_matrix()
                py5.translate(h/2 + 1, 0, 0)
                py5.no_fill()
                py5.stroke_weight(2)
                col = CYAN if mid_t < py5.PI/2 else MAGENTA
                alpha = py5.lerp(100, 255, (py5.sin(time_val * 4 + mid_t * 10) + 1) / 2)
                py5.stroke(*col, alpha)
                
                # Draw a "circuit" line
                py5.begin_shape()
                py5.vertex(0, -box_h/3, -box_w/3)
                py5.vertex(0, box_h/3, -box_w/3)
                py5.vertex(0, box_h/3, box_h/3)
                py5.end_shape()
                py5.pop_matrix()
                
            py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global stars, root_quads
    stars = np.random.uniform(-2000, 2000, (STAR_COUNT, 3))
    
    # Root quads cover the sphere
    root_quads = []
    div_t, div_p = 4, 8
    for i in range(div_t):
        for j in range(div_p):
            t0 = (i / div_t) * py5.PI
            t1 = ((i + 1) / div_t) * py5.PI
            p0 = (j / div_p) * py5.TWO_PI
            p1 = ((j + 1) / div_p) * py5.TWO_PI
            root_quads.append(ShellQuad(t0, t1, p0, p1, 0))

def draw():
    py5.background(0, 0, 10)
    py5.ambient_light(50, 50, 60)
    py5.point_light(255, 255, 255, 0, 0, 0)
    
    time_val = py5.frame_count / 60.0
    core_pulse = (py5.sin(time_val * 2.5) + 1) / 2
    
    # Camera
    cam_dist = 900 + py5.sin(time_val * 0.3) * 100
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               300 * py5.sin(time_val * 0.15), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # Starfield
    py5.stroke(200, 200, 255, 150)
    py5.stroke_weight(1)
    for s in stars:
        # Subtle twinkling
        twinkle = py5.noise(s[0], s[1], time_val)
        if twinkle > 0.4:
            py5.point(*s)
            
    # Central Star Core
    py5.push_matrix()
    py5.no_stroke()
    for i in range(5):
        r = CORE_RADIUS * (1.0 + core_pulse * 0.15) * (1.0 - i * 0.15)
        alpha = 50 + 100 * (1.0 - i/5.0)
        py5.fill(255, 255, 200 - i*20, alpha)
        py5.sphere(r)
    py5.pop_matrix()
    
    # Shell
    py5.rotate_y(time_val * 0.05)
    for quad in root_quads:
        quad.render(time_val, core_pulse)
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "8M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
