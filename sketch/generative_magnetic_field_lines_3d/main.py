from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 6000
particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for _ in range(num_particles):
        spawn_particle()

def spawn_particle():
    x = py5.random(-300, 300)
    y = py5.random(-300, 300)
    z = py5.random(-300, 300)
    age = 0
    max_age = py5.random(20, 80)
    h = py5.random(180, 300)
    particles.append([x, y, z, age, max_age, h])

def draw():
    py5.push_matrix()
    py5.translate(0, 0, -800)
    py5.push_style()
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(-py5.width, -py5.height, py5.width * 3, py5.height * 3)
    py5.pop_style()
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(py5.frame_count * 0.015)
    py5.rotate_x(py5.sin(py5.frame_count * 0.005) * 0.5)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.5)
    
    p1 = np.array([0, 400 * py5.sin(py5.frame_count * 0.03), 0])
    p2 = np.array([0, -400 * py5.sin(py5.frame_count * 0.03), 0])
    
    new_particles = []
    
    for p in particles:
        pos = np.array([p[0], p[1], p[2]])
        
        r1 = pos - p1
        d1 = np.linalg.norm(r1) + 1.0
        f1 = (r1 / d1**3) * 200000
        
        r2 = pos - p2
        d2 = np.linalg.norm(r2) + 1.0
        f2 = -(r2 / d2**3) * 200000
        
        force = f1 + f2
        mag = np.linalg.norm(force)
        if mag > 20:
            force = (force / mag) * 20
            
        npos = pos + force
        
        py5.stroke(p[5], 90, 90, py5.remap(p[3], 0, p[4], 80, 0))
        py5.line(pos[0], pos[1], pos[2], npos[0], npos[1], npos[2])
        
        p[0], p[1], p[2] = npos
        p[3] += 1
        
        if p[3] < p[4] and mag < 200:
            new_particles.append(p)
    
    particles[:] = new_particles
    
    while len(particles) < num_particles:
        spawn_particle()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
            
        import os
        os._exit(0)

py5.run_sketch()
