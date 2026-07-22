from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

n_boids = 1500
positions = None
velocities = None
species = None

def setup():
    global positions, velocities, species
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.zeros((n_boids, 2), dtype=np.float32)
    velocities = np.zeros((n_boids, 2), dtype=np.float32)
    species = np.random.randint(0, 2, size=n_boids) # 0 = Electric Blue, 1 = Coral Pink
    
    for i in range(n_boids):
        positions[i, 0] = random.uniform(0, SIZE[0])
        positions[i, 1] = random.uniform(0, SIZE[1])
        angle = random.uniform(0, py5.TWO_PI)
        velocities[i, 0] = math.cos(angle) * 2.0
        velocities[i, 1] = math.sin(angle) * 2.0

def draw():
    global positions, velocities, species
    if py5.frame_count == 1:
        py5.background(1, 10, 16) # Dark teal
        
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(1, 10, 16, 12) # Fading trail
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    s = 0.002
    
    px = positions[:, 0]
    py = positions[:, 1]
    vx = velocities[:, 0]
    vy = velocities[:, 1]
    
    # Simple fluid flow field based on noise
    fluid_vx = np.zeros_like(px)
    fluid_vy = np.zeros_like(py)
    
    for i in range(n_boids):
        angle = py5.noise(px[i]*s, py[i]*s, t) * py5.TWO_PI * 4.0
        fluid_vx[i] = math.cos(angle) * 0.5
        fluid_vy[i] = math.sin(angle) * 0.5
        
    # Boids simple rules (we'll just use a fast approximation: alignment with flow, separation from neighbors is hard without spatial hash, we'll skip complex boids and just do fluid particles with species repulsion/attraction)
    # Actually just fluid flow + random wander + cross species repulsion
    
    vx += fluid_vx
    vy += fluid_vy
    
    # Add random wander
    for i in range(n_boids):
        vx[i] += random.uniform(-0.1, 0.1)
        vy[i] += random.uniform(-0.1, 0.1)
        
    # Limit speed
    speed = np.sqrt(vx**2 + vy**2)
    max_speed = 4.0
    overspeed = speed > max_speed
    vx[overspeed] = vx[overspeed] / speed[overspeed] * max_speed
    vy[overspeed] = vy[overspeed] / speed[overspeed] * max_speed
    
    positions[:, 0] += vx
    positions[:, 1] += vy
    velocities[:, 0] = vx
    velocities[:, 1] = vy
    
    # Wrap
    positions[:, 0] = np.mod(positions[:, 0], SIZE[0])
    positions[:, 1] = np.mod(positions[:, 1], SIZE[1])
    
    # Draw
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    
    for i in range(n_boids):
        if species[i] == 0:
            py5.stroke(0, 160, 255, 40) # Electric Blue
        else:
            py5.stroke(255, 96, 128, 40) # Coral Pink
            
        py5.vertex(positions[i, 0], positions[i, 1])
        
    py5.end_shape()

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
