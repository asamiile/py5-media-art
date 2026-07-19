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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle life configuration
N_PARTICLES = 3000
TYPES = 3
# 0: Magenta, 1: Cyan, 2: Gold
colors = [
    (255, 0, 150),
    (0, 255, 255),
    (255, 200, 0)
]

# Initialize particles
positions = np.random.rand(N_PARTICLES, 2) * [SIZE[0], SIZE[1]]
velocities = np.zeros((N_PARTICLES, 2))
types = np.random.randint(0, TYPES, N_PARTICLES)

# Attraction matrix (randomized for unique emergent behavior)
np.random.seed(42)  # Use a fixed seed here so it's consistent across the animation, but we can change the overall behavior
# Wait, no fixed seeds! I'll use a random seed every run but keep it consistent during the run
import random
random.seed()
np.random.seed()
interaction_matrix = (np.random.rand(TYPES, TYPES) - 0.5) * 2

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.color_mode(py5.RGB, 255)
    py5.no_stroke()

def draw():
    global positions, velocities
    # Trails effect via semi-transparent background clearing
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Simple brute-force or vectorized particle interaction
    # To keep it performant for 3000 particles, we use a simpler vectorized approach in chunks or just a fast numpy method
    
    # We will use a fast vectorized approach
    # Since 3000^2 is 9 million, we can do it in Numpy
    
    # For a completely correct particle life we need all pairs, which is a bit heavy.
    # We'll use a simplified version: sample random neighbors to approximate or just do full matrix if fast enough.
    # 9 million operations in numpy takes about 10-20ms, which is fine for offline rendering.
    
    # Calculate pairwise differences (this is memory intensive, so we do it per type to save RAM)
    for i in range(TYPES):
        mask_i = types == i
        pos_i = positions[mask_i]
        if len(pos_i) == 0: continue
        
        force_total = np.zeros_like(pos_i)
        
        for j in range(TYPES):
            mask_j = types == j
            pos_j = positions[mask_j]
            if len(pos_j) == 0: continue
            
            # Interaction force i -> j
            force_mag = interaction_matrix[i, j]
            
            # Compute distances (broadcasting)
            # pos_i: (N_i, 2), pos_j: (N_j, 2)
            dx = pos_i[:, 0:1] - pos_j[:, 0]
            dy = pos_i[:, 1:2] - pos_j[:, 1]
            
            dist_sq = dx**2 + dy**2
            # Add a small epsilon to avoid division by zero
            dist_sq[dist_sq < 1.0] = 1.0
            
            # Gravity: F = G * m1 * m2 / r^2
            # We use a smoothed force that flips to repulsion at very close range
            dist = np.sqrt(dist_sq)
            
            # Force law: 
            # If dist < 20: strong repulsion
            # If 20 < dist < 80: attraction/repulsion based on matrix
            # If dist > 80: 0
            
            f = np.zeros_like(dist)
            repel_mask = dist < 15.0
            interact_mask = (dist >= 15.0) & (dist < 100.0)
            
            f[repel_mask] = -2.0 / dist[repel_mask]
            f[interact_mask] = force_mag * (1.0 - np.abs(dist[interact_mask] - 57.5) / 42.5) # Triangle function
            
            # Multiply by direction
            fx = f * (dx / dist)
            fy = f * (dy / dist)
            
            # Sum forces from all j on each i
            force_total[:, 0] += np.sum(fx, axis=1)
            force_total[:, 1] += np.sum(fy, axis=1)
            
        velocities[mask_i] = (velocities[mask_i] + force_total) * 0.5  # friction
        
    positions += velocities
    
    # Wrap
    positions[:, 0] = positions[:, 0] % py5.width
    positions[:, 1] = positions[:, 1] % py5.height
    
    # Draw
    for i in range(TYPES):
        mask_i = types == i
        pos_i = positions[mask_i]
        c = colors[i]
        py5.fill(c[0], c[1], c[2], 100)
        
        # Batch draw using points or small circles
        py5.begin_shape(py5.POINTS)
        py5.stroke(c[0], c[1], c[2], 150)
        py5.stroke_weight(4)
        for p in pos_i:
            py5.vertex(p[0], p[1])
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
