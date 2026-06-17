from pathlib import Path
import shutil
import subprocess
import sys
import random
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

NUM_PARTICLES = 5000
particles = None

def setup():
    global particles
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # [x, y, z, vx, vy, vz]
    particles = np.zeros((NUM_PARTICLES, 6))
    
    # Initialize in a torus shape
    angles1 = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    angles2 = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    R = 400
    r = 100
    
    particles[:, 0] = (R + r * np.cos(angles2)) * np.cos(angles1)
    particles[:, 1] = (R + r * np.cos(angles2)) * np.sin(angles1)
    particles[:, 2] = r * np.sin(angles2)

def draw():
    global particles
    
    py5.background(0, 0, 0, 30)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.01
    
    py5.rotate_x(py5.PI / 4 + py5.sin(t) * 0.2)
    py5.rotate_z(t * 0.5)
    
    # Numpy calculations for particle physics
    px = particles[:, 0]
    py = particles[:, 1]
    pz = particles[:, 2]
    
    # Two massive rotating planetary gears
    g1_x = 300 * np.cos(t * 2)
    g1_y = 300 * np.sin(t * 2)
    g1_z = 100 * np.sin(t)
    
    g2_x = 300 * np.cos(t * 2 + np.pi)
    g2_y = 300 * np.sin(t * 2 + np.pi)
    g2_z = 100 * np.sin(t + np.pi)
    
    # Gravitational pull towards gears
    dx1 = g1_x - px
    dy1 = g1_y - py
    dz1 = g1_z - pz
    dist1 = np.sqrt(dx1**2 + dy1**2 + dz1**2) + 1.0
    
    dx2 = g2_x - px
    dy2 = g2_y - py
    dz2 = g2_z - pz
    dist2 = np.sqrt(dx2**2 + dy2**2 + dz2**2) + 1.0
    
    particles[:, 3] += dx1 / (dist1**1.5) * 50.0 + dx2 / (dist2**1.5) * 50.0
    particles[:, 4] += dy1 / (dist1**1.5) * 50.0 + dy2 / (dist2**1.5) * 50.0
    particles[:, 5] += dz1 / (dist1**1.5) * 50.0 + dz2 / (dist2**1.5) * 50.0
    
    # Swirling drag (curl)
    particles[:, 3] += -py * 0.005
    particles[:, 4] += px * 0.005
    
    # Center attraction to prevent flying off
    dist_origin = np.sqrt(px**2 + py**2 + pz**2) + 1.0
    particles[:, 3] -= px / dist_origin * 2.0
    particles[:, 4] -= py / dist_origin * 2.0
    particles[:, 5] -= pz / dist_origin * 2.0
    
    # Friction
    particles[:, 3] *= 0.95
    particles[:, 4] *= 0.95
    particles[:, 5] *= 0.95
    
    particles[:, 0] += particles[:, 3]
    particles[:, 1] += particles[:, 4]
    particles[:, 2] += particles[:, 5]
    
    # Draw central gear rings
    py5.stroke(200, 80, 100, 50)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.push_matrix()
    py5.rotate_z(-t)
    for r in range(150, 250, 10):
        py5.ellipse(0, 0, r*2, r*2)
    py5.pop_matrix()
    
    # Rendering particles
    py5.stroke_weight(3)
    for p in particles:
        speed = np.sqrt(p[3]**2 + p[4]**2 + p[5]**2)
        hue = (180 + speed * 10) % 360
        py5.stroke(hue, 80, 100, 80)
        py5.point(p[0], p[1], p[2])
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
