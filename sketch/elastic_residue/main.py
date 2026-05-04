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

# Simulation constants
COLS, ROWS = 30, 30
SPACING = 40
SPRING_STRENGTH = 0.5
SOLVER_ITERATIONS = 4
DRAG = 0.015
SIM_STEPS = 2

class Particle:
    def __init__(self, x, y):
        self.pos = py5.Py5Vector(x, y)
        self.prev = py5.Py5Vector(x, y)
        self.acc = py5.Py5Vector(0, 0)
        self.locked = False

    def update(self):
        if self.locked: return
        v = (self.pos - self.prev) * (1.0 - DRAG)
        tmp = self.pos.copy
        self.pos += v + self.acc
        self.prev = tmp
        self.acc *= 0

class Spring:
    def __init__(self, a, b, length):
        self.a = a
        self.b = b
        self.rest = length

    def resolve(self):
        delta = self.b.pos - self.a.pos
        d = delta.mag
        if d == 0: return
        diff = (d - self.rest) / d
        corr = delta * (0.5 * SPRING_STRENGTH * diff)
        if not self.a.locked: self.a.pos += corr
        if not self.b.locked: self.b.pos -= corr
        return diff # return tension

particles = []
springs = []
buffer = None

def setup():
    global buffer
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize grid
    start_x = (py5.width - (COLS-1)*SPACING) / 2
    start_y = (py5.height - (ROWS-1)*SPACING) / 2
    
    for j in range(ROWS):
        row = []
        for i in range(COLS):
            p = Particle(start_x + i * SPACING, start_y + j * SPACING)
            # Lock corners
            if (i == 0 and j == 0) or (i == COLS-1 and j == 0) or \
               (i == 0 and j == ROWS-1) or (i == COLS-1 and j == ROWS-1):
                p.locked = True
            row.append(p)
        particles.append(row)
        
    for j in range(ROWS):
        for i in range(COLS):
            a = particles[j][i]
            if i < COLS-1: springs.append(Spring(a, particles[j][i+1], SPACING))
            if j < ROWS-1: springs.append(Spring(a, particles[j+1][i], SPACING))
            # Diagonals for stability
            if i < COLS-1 and j < ROWS-1:
                springs.append(Spring(a, particles[j+1][i+1], SPACING * 1.414))
    
    buffer = py5.create_graphics(py5.width, py5.height, py5.P2D)
    buffer.begin_draw()
    buffer.background(26, 15, 5) # Deep sienna
    buffer.end_draw()

def draw():
    t = py5.frame_count * 0.02
    
    # Interaction: Pressure spheres
    spheres = []
    num_s = 3
    for i in range(num_s):
        sx = py5.width/2 + py5.cos(t * (0.5 + i*0.2)) * 400
        sy = py5.height/2 + py5.sin(t * (0.7 - i*0.1)) * 300
        spheres.append(py5.Py5Vector(sx, sy))
        
    # Simulation steps
    for _ in range(SIM_STEPS):
        for row in particles:
            for p in row:
                # Wind/Noise force
                noise_f = (py5.noise(p.pos.x*0.01, p.pos.y*0.01, t) - 0.5) * 0.1
                p.acc += py5.Py5Vector(noise_f, 0.05) # Gravity
                
                # Sphere repulsion
                for s in spheres:
                    d_vec = p.pos - s
                    dist = d_vec.mag
                    if dist < 150:
                        p.acc += d_vec.normalize() * (150 - dist) * 0.05
                p.update()
        
        for _ in range(SOLVER_ITERATIONS):
            for s in springs:
                s.resolve()

    # Draw to buffer (residue)
    buffer.begin_draw()
    buffer.stroke_weight(1)
    for s in springs:
        tension = abs((s.b.pos - s.a.pos).mag - s.rest) / SPACING
        if tension > 0.05:
            # Persistent glow
            buffer.stroke(255, 215, 0, 5) # Gold
            buffer.line(s.a.pos.x, s.a.pos.y, s.b.pos.x, s.b.pos.y)
    buffer.end_draw()
    
    # Render
    py5.image(buffer, 0, 0)
    
    # Draw current mesh
    py5.no_fill()
    for s in springs:
        tension = abs((s.b.pos - s.a.pos).mag - s.rest) / SPACING
        # Tan to Gold based on tension
        c = py5.lerp_color(py5.color(210, 180, 140, 40), py5.color(255, 215, 0, 150), min(1.0, tension*3))
        py5.stroke(c)
        py5.stroke_weight(py5.lerp(0.5, 2.5, min(1.0, tension*2)))
        py5.line(s.a.pos.x, s.a.pos.y, s.b.pos.x, s.b.pos.y)

    # Save frames and export
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "5000k",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
