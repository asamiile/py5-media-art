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

NUM_PARTICLES = 15000
particles = None
colors = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, colors
    # [x, y, z, vx, vy, vz]
    particles = np.zeros((NUM_PARTICLES, 6), dtype=np.float32)
    colors = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    
    # Spawn particles in a cylinder volume
    for i in range(NUM_PARTICLES):
        spawn_particle(i)

def spawn_particle(i):
    angle = np.random.rand() * py5.TWO_PI
    radius = np.random.rand() * 400
    particles[i, 0] = np.cos(angle) * radius
    particles[i, 1] = np.sin(angle) * radius
    particles[i, 2] = -1000 + np.random.rand() * 2000
    
    particles[i, 3] = 0
    particles[i, 4] = 0
    particles[i, 5] = 10 + np.random.rand() * 5
    
    # Assign color based on starting angle and radius
    if radius < 150:
        colors[i] = [0, 255, 255] # Cyan
    elif angle < py5.PI:
        colors[i] = [255, 0, 255] # Magenta
    else:
        colors[i] = [0, 255, 100] # Toxic green

def draw():
    global particles
    py5.background(5, 5, 10)
    
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    time_val = py5.frame_count * 0.01
    
    # Slow camera movement
    py5.rotate_x(0.3 + np.sin(time_val)*0.1)
    py5.rotate_y(time_val * 0.3)
    
    py5.blend_mode(py5.ADD)
    
    px = particles[:, 0]
    py = particles[:, 1]
    pz = particles[:, 2]
    vx = particles[:, 3]
    vy = particles[:, 4]
    vz = particles[:, 5]
    
    # Flow field based on 3D noise
    for i in range(NUM_PARTICLES):
        n1 = py5.os_noise(px[i]*0.005, py[i]*0.005, pz[i]*0.005 + time_val)
        n2 = py5.os_noise(px[i]*0.005 + 100, py[i]*0.005 + 100, pz[i]*0.005 + time_val)
        
        # Swirl forces
        fx = (n1 - 0.5) * 2.0
        fy = (n2 - 0.5) * 2.0
        
        vx[i] += fx
        vy[i] += fy
        
        # Friction
        vx[i] *= 0.95
        vy[i] *= 0.95
        
    px += vx
    py += vy
    pz += vz
    
    # Wrap particles when they leave the pipe
    respawn_mask = pz > 1000
    for i in np.where(respawn_mask)[0]:
        spawn_particle(i)
        pz[i] = -1000 # Reset to back of pipe
        
    particles[:, 0] = px
    particles[:, 1] = py
    particles[:, 2] = pz
    particles[:, 3] = vx
    particles[:, 4] = vy
    particles[:, 5] = vz
    
    py5.stroke_weight(2)
    
    # Draw tails using line from (px, py, pz) back along velocity
    for i in range(NUM_PARTICLES):
        c = colors[i]
        py5.stroke(c[0], c[1], c[2], 80)
        
        py5.line(px[i], py[i], pz[i], 
                 px[i] - vx[i]*3, py[i] - vy[i]*3, pz[i] - vz[i]*3)
        
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
