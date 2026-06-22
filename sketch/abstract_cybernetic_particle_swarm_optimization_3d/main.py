from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random
import math
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 300
particles = []

def fitness(x, y, z, t):
    # A moving complex landscape based on noise
    val = py5.os_noise(x * 0.002, y * 0.002 + t * 0.01, z * 0.002)
    val += py5.os_noise(x * 0.01 - t * 0.02, y * 0.01, z * 0.01) * 0.5
    # Attract to center somewhat to keep them on screen
    dist = math.sqrt(x*x + y*y + z*z)
    val -= (dist / 2000.0) 
    return val

class Particle:
    def __init__(self):
        self.pos = np.array([random.uniform(-500, 500), random.uniform(-500, 500), random.uniform(-500, 500)])
        self.vel = np.array([random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5)])
        self.pbest_pos = self.pos.copy()
        self.pbest_val = -float('inf')
        self.history = []

global_best_pos = np.zeros(3)
global_best_val = -float('inf')

for _ in range(NUM_PARTICLES):
    particles.append(Particle())

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global global_best_pos, global_best_val
    
    # Motion blur using transparent rect over everything - wait, in P3D transparent background doesn't work perfectly,
    # but we can draw a large box or just redraw black with alpha. Or just clear background and draw history.
    py5.background(0, 0, 5)
    
    t = py5.frame_count
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -500)
    
    py5.rotate_y(t * 0.005)
    py5.rotate_x(py5.sin(t * 0.003) * 0.2)
    
    # PSO Update
    global_best_val = -float('inf') # Recalculate each frame since landscape moves
    
    w = 0.7  # inertia
    c1 = 1.5 # cognitive
    c2 = 1.5 # social
    
    for p in particles:
        val = fitness(p.pos[0], p.pos[1], p.pos[2], t)
        
        if val > p.pbest_val:
            p.pbest_val = val
            p.pbest_pos = p.pos.copy()
            
        if val > global_best_val:
            global_best_val = val
            global_best_pos = p.pos.copy()
            
    for p in particles:
        r1 = random.random()
        r2 = random.random()
        
        cognitive_vel = c1 * r1 * (p.pbest_pos - p.pos)
        social_vel = c2 * r2 * (global_best_pos - p.pos)
        
        p.vel = w * p.vel + cognitive_vel + social_vel
        
        # Limit velocity
        speed = np.linalg.norm(p.vel)
        if speed > 20:
            p.vel = (p.vel / speed) * 20
            
        p.pos += p.vel
        
        p.history.append(p.pos.copy())
        if len(p.history) > 30:
            p.history.pop(0)
            
    # Draw particles and trails
    py5.stroke_weight(2)
    py5.no_fill()
    
    for p in particles:
        speed = np.linalg.norm(p.vel)
        hue = (180 + speed * 10) % 360
        
        py5.begin_shape(py5.LINE_STRIP)
        for i, hpos in enumerate(p.history):
            alpha = py5.remap(i, 0, len(p.history), 0, 255)
            py5.stroke(hue, 80, 100, alpha)
            py5.vertex(hpos[0], hpos[1], hpos[2])
        py5.end_shape()
        
        # Draw head
        py5.push_matrix()
        py5.translate(p.pos[0], p.pos[1], p.pos[2])
        py5.no_stroke()
        py5.fill(hue, 50, 100)
        py5.box(4)
        py5.pop_matrix()

    # Draw global best indicator
    py5.push_matrix()
    py5.translate(global_best_pos[0], global_best_pos[1], global_best_pos[2])
    py5.no_fill()
    py5.stroke(0, 0, 100, 150)
    py5.stroke_weight(1)
    py5.sphere_detail(8)
    py5.sphere(30 + py5.sin(t * 0.5) * 10)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
