from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.spatial.distance import cdist

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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
N_BODIES = 4000
G = 2.0
SOFTENING = 20.0

def create_galaxy(n, center, radius, mass, speed_mult, color_class):
    # Random points in a disk
    r = np.random.triangular(0, radius, radius, size=n)
    theta = np.random.rand(n) * 2 * np.pi
    
    x = center[0] + r * np.cos(theta)
    y = center[1] + r * np.sin(theta)
    pos = np.column_stack((x, y))
    
    # Orbital velocity v = sqrt(G * M / r)
    v_mag = np.sqrt(G * mass / (r + SOFTENING)) * speed_mult
    # Perpendicular vector for orbit
    vx = -np.sin(theta) * v_mag
    vy = np.cos(theta) * v_mag
    vel = np.column_stack((vx, vy))
    
    c_class = np.full(n, color_class, dtype=np.int32)
    return pos, vel, c_class

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, color_classes
    
    # Create two colliding galaxies
    cx1, cy1 = py5.width * 0.3, py5.height * 0.7
    cx2, cy2 = py5.width * 0.7, py5.height * 0.3
    
    n1 = N_BODIES // 2
    n2 = N_BODIES - n1
    
    p1, v1, c1 = create_galaxy(n1, (cx1, cy1), 400, 50000, 1.2, 0)
    p2, v2, c2 = create_galaxy(n2, (cx2, cy2), 300, 30000, 1.0, 1)
    
    # Give them a slight push towards each other
    v1[:, 0] += 2.0
    v1[:, 1] -= 2.0
    v2[:, 0] -= 1.0
    v2[:, 1] += 1.0
    
    pos = np.vstack((p1, p2))
    vel = np.vstack((v1, v2))
    color_classes = np.concatenate((c1, c2))

def draw():
    global pos, vel
    
    # Motion blur / glowing trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Vectorized Gravity
    # Compute differences and distances
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :] # (N, N, 2)
    dist_sq = np.sum(diff**2, axis=-1) # (N, N)
    
    # F = G * m1 * m2 / (r^2 + softening^2)
    # Since all masses are 1, acceleration is just sum of forces
    force_mag = G / (dist_sq + SOFTENING**2)
    np.fill_diagonal(force_mag, 0)
    
    # Normalize diff vectors
    dist = np.sqrt(dist_sq)
    dist[dist == 0] = 1 # Avoid div by zero
    diff_norm = diff / dist[:, :, np.newaxis]
    
    # Multiply magnitude by direction and sum
    accel = np.sum(-diff_norm * force_mag[:, :, np.newaxis], axis=1)
    
    # Euler integration
    vel += accel
    pos += vel
    
    # Additive glowing trails
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    palette = [
        (255, 100, 50, 40), # Bright orange/red
        (50, 100, 255, 40), # Deep blue/cyan
    ]
    
    for i in range(2):
        mask = (color_classes == i)
        if np.any(mask):
            py5.stroke(*palette[i])
            py5.points(pos[mask])
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
