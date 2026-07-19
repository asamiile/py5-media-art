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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 40000
particles = np.random.uniform(0, 1.0, (NUM_PARTICLES, 2)).astype(np.float32)
particles[:, 0] *= SIZE[0]
particles[:, 1] *= SIZE[1]

energy = np.random.uniform(0.1, 1.0, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 5, 10)
    
def draw():
    global particles, energy
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 5, 10, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.01
    
    pole1 = np.array([SIZE[0] * 0.4 + np.sin(t*0.5)*400, SIZE[1] * 0.5 + np.cos(t*0.7)*300])
    pole2 = np.array([SIZE[0] * 0.6 + np.sin(t*0.6 + py5.PI)*400, SIZE[1] * 0.5 + np.cos(t*0.4)*300])
    pole3 = np.array([SIZE[0] * 0.5 + np.sin(t*0.3)*200, SIZE[1] * 0.5 + np.cos(t*0.9)*500])
    
    poles = [pole1, pole2, pole3]
    charges = [1.0, -1.0, 0.5]
    
    x = particles[:, 0]
    y = particles[:, 1]
    
    dx = np.zeros_like(x)
    dy = np.zeros_like(y)
    
    for i, p in enumerate(poles):
        dx_p = p[0] - x
        dy_p = p[1] - y
        dist_sq = dx_p**2 + dy_p**2 + 10000.0
        
        force = charges[i] * 500000.0 / dist_sq
        
        dx += -dy_p * force * 0.02 + dx_p * force * 0.01
        dy += dx_p * force * 0.02 + dy_p * force * 0.01
    
    noise_x = py5.os_noise(x * 0.002, y * 0.002, t) - 0.5
    noise_y = py5.os_noise(x * 0.002 + 100, y * 0.002 + 100, t) - 0.5
    
    dx += noise_x * 20.0
    dy += noise_y * 20.0
    
    particles[:, 0] += dx
    particles[:, 1] += dy
    
    vel_mag = np.sqrt(dx**2 + dy**2)
    energy = np.clip(vel_mag * 0.05, 0, 1)
    
    out_of_bounds = (particles[:, 0] < 0) | (particles[:, 0] > SIZE[0]) | (particles[:, 1] < 0) | (particles[:, 1] > SIZE[1])
    respawn = out_of_bounds | (energy < 0.05) | (np.random.random(NUM_PARTICLES) < 0.01)
    
    num_respawn = np.sum(respawn)
    if num_respawn > 0:
        particles[respawn, 0] = np.random.uniform(0, SIZE[0], num_respawn)
        particles[respawn, 1] = np.random.uniform(0, SIZE[1], num_respawn)
        energy[respawn] = 0.5
        
    screen_coords = particles
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    high = energy > 0.7
    if np.any(high):
        py5.stroke(255, 255, 200, 150)
        py5.points(screen_coords[high])
        
    med = (energy <= 0.7) & (energy > 0.3)
    if np.any(med):
        py5.stroke(255, 100, 20, 80)
        py5.points(screen_coords[med])
        
    low = energy <= 0.3
    if np.any(low):
        py5.stroke(100, 20, 80, 40)
        py5.points(screen_coords[low])

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
