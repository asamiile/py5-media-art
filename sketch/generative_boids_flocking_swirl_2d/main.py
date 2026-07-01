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
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Boids simulation parameters
N_BOIDS = 3000
MAX_SPEED = 8.0
MAX_FORCE = 0.5
PERCEPTION = 100.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, acc
    pos = np.random.rand(N_BOIDS, 2) * [py5.width, py5.height]
    vel = (np.random.rand(N_BOIDS, 2) - 0.5) * MAX_SPEED
    acc = np.zeros((N_BOIDS, 2))

def limit_vector(v, max_val):
    magnitudes = np.linalg.norm(v, axis=1, keepdims=True)
    # Avoid division by zero
    magnitudes[magnitudes == 0] = 1.0
    scale = np.minimum(1.0, max_val / magnitudes)
    return v * scale

def draw():
    global pos, vel, acc
    
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 40) # Trails
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Target that moves in a Lissajous curve
    target_x = py5.width/2 + py5.width/3 * np.sin(t * py5.TWO_PI * 1.5)
    target_y = py5.height/2 + py5.height/3 * np.cos(t * py5.TWO_PI * 2.0)
    
    # Simple vectorization for boids is O(N^2) which is slow for N=3000 in pure python/numpy
    # To keep it fast enough for 4K 30fps rendering without CUDA, we'll use a trick:
    # Instead of all-to-all, we'll only check a random subset of neighbors each frame!
    # Or, we can use a simpler target-following + noise instead of true O(N^2) flocking.
    
    # Simpler Flow Field + Target Seeking + Noise (Pseudo-Flocking)
    # This gives a beautiful flocking effect in O(N) time!
    
    # 1. Flow Field (Perlin noise)
    # We don't have vectorized 2D noise in py5 directly, so we use a sine-wave interference field
    flow_x = np.sin(pos[:, 1] * 0.005 + t * 10) * 0.5 + np.cos(pos[:, 0] * 0.003 - t * 5) * 0.5
    flow_y = np.cos(pos[:, 0] * 0.005 - t * 8) * 0.5 + np.sin(pos[:, 1] * 0.004 + t * 6) * 0.5
    flow = np.column_stack((flow_x, flow_y)) * 2.0
    
    # 2. Target Seeking
    dir_to_target = np.column_stack((target_x - pos[:, 0], target_y - pos[:, 1]))
    dist_to_target = np.linalg.norm(dir_to_target, axis=1, keepdims=True)
    dist_to_target[dist_to_target == 0] = 1.0
    dir_to_target = (dir_to_target / dist_to_target) * MAX_SPEED
    seek = dir_to_target - vel
    seek = limit_vector(seek, MAX_FORCE * 1.5)
    
    # 3. Swirl (Vortex around center)
    vortex_x = -(pos[:, 1] - py5.height/2)
    vortex_y = (pos[:, 0] - py5.width/2)
    vortex = np.column_stack((vortex_x, vortex_y))
    vortex_mag = np.linalg.norm(vortex, axis=1, keepdims=True)
    vortex_mag[vortex_mag == 0] = 1.0
    vortex = (vortex / vortex_mag) * MAX_SPEED
    vortex_force = limit_vector(vortex - vel, MAX_FORCE)
    
    # Apply forces
    acc = flow + seek * 1.0 + vortex_force * 0.5
    
    # Update velocity
    vel += acc
    vel = limit_vector(vel, MAX_SPEED)
    
    # Update position
    pos += vel
    
    # Wrapping bounds
    pos[:, 0] = pos[:, 0] % py5.width
    pos[:, 1] = pos[:, 1] % py5.height
    
    # Draw boids
    # We will use points with varying colors for speed
    
    # Color based on velocity
    vel_mag = np.linalg.norm(vel, axis=1)
    
    # Fast = Cyan, Slow = Magenta
    # Using multiple begin_shape/end_shape would be slow,
    # so we group them by roughly 3 speed buckets.
    
    bucket_slow = vel_mag < (MAX_SPEED * 0.6)
    bucket_med = (vel_mag >= (MAX_SPEED * 0.6)) & (vel_mag < (MAX_SPEED * 0.85))
    bucket_fast = vel_mag >= (MAX_SPEED * 0.85)
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    # Magenta (Slow)
    py5.stroke(255, 50, 200, 200)
    py5.begin_shape(py5.POINTS)
    py5.vertices(pos[bucket_slow])
    py5.end_shape()
    
    # Violet (Med)
    py5.stroke(150, 100, 255, 200)
    py5.begin_shape(py5.POINTS)
    py5.vertices(pos[bucket_med])
    py5.end_shape()
    
    # Cyan (Fast)
    py5.stroke(50, 255, 255, 200)
    py5.begin_shape(py5.POINTS)
    py5.vertices(pos[bucket_fast])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
