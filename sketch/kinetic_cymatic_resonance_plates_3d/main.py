from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

NUM_PARTICLES = 10000
particles = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles
    # x, y, z, vx, vy, vz
    particles = np.zeros((NUM_PARTICLES, 6), dtype=np.float32)
    # random placement on a 2D plane
    particles[:, 0] = (np.random.rand(NUM_PARTICLES) - 0.5) * 800
    particles[:, 1] = (np.random.rand(NUM_PARTICLES) - 0.5) * 800

def chladni_plate(x, y, t):
    # Scale coordinates
    sx, sy = x * 0.01, y * 0.01
    
    # Frequencies morphing over time
    n1 = 2 + np.sin(t * 0.5) * 1.5
    m1 = 3 + np.cos(t * 0.4) * 1.5
    
    val = np.cos(n1 * sx) * np.cos(m1 * sy) - np.cos(m1 * sx) * np.cos(n1 * sy)
    return val

def draw():
    global particles
    py5.background(15, 15, 20)
    
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 100, -200)
    
    time_val = py5.frame_count * 0.02
    
    py5.rotate_x(1.0)
    py5.rotate_z(time_val * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Update particles
    px = particles[:, 0]
    py = particles[:, 1]
    pz = particles[:, 2]
    
    vx = particles[:, 3]
    vy = particles[:, 4]
    vz = particles[:, 5]
    
    # The vibration of the plate
    plate_force = chladni_plate(px, py, time_val)
    
    # Calculate gradient of the plate to push particles towards the nodal lines
    eps = 0.5
    grad_x = chladni_plate(px + eps, py, time_val) - chladni_plate(px - eps, py, time_val)
    grad_y = chladni_plate(px, py + eps, time_val) - chladni_plate(px, py - eps, time_val)
    
    # If a particle is on a vibrating part (abs(plate_force) > threshold), it gets launched up
    vibrating_mask = np.abs(plate_force) > 0.1
    
    # Launch vibrating particles
    vz[vibrating_mask] += np.abs(plate_force[vibrating_mask]) * 5.0
    
    # Push away from anti-nodes
    vx -= grad_x * 2.0
    vy -= grad_y * 2.0
    
    # Gravity
    vz -= 1.5
    
    # Update positions
    px += vx
    py += vy
    pz += vz
    
    # Floor collision
    floor_mask = pz < 0
    pz[floor_mask] = 0
    vz[floor_mask] *= -0.5
    
    # Friction
    vx *= 0.95
    vy *= 0.95
    
    # Keep on plate
    r_sq = px**2 + py**2
    off_plate = r_sq > 400**2
    
    # Respawn off plate particles
    if np.any(off_plate):
        n_off = np.sum(off_plate)
        px[off_plate] = (np.random.rand(n_off) - 0.5) * 800
        py[off_plate] = (np.random.rand(n_off) - 0.5) * 800
        pz[off_plate] = 100
        vx[off_plate] = 0
        vy[off_plate] = 0
        vz[off_plate] = 0
        
    particles[:, 0] = px
    particles[:, 1] = py
    particles[:, 2] = pz
    particles[:, 3] = vx
    particles[:, 4] = vy
    particles[:, 5] = vz
    
    # Draw Plate
    py5.stroke(100, 100, 150, 40)
    py5.no_fill()
    py5.circle(0, 0, 800)
    
    py5.no_stroke()
    
    # Draw particles
    py5.fill(255, 200, 50, 180) # Golden amber
    
    for i in range(NUM_PARTICLES):
        py5.push_matrix()
        py5.translate(px[i], py[i], pz[i])
        py5.circle(0, 0, 3)
        py5.pop_matrix()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
