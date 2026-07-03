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

# Particle Life Simulation
NUM_TYPES = 4
# Adjust number of particles to ensure real-time performance of O(N^2) in numpy
NUM_PER_TYPE = 1200
NUM_PARTICLES = NUM_TYPES * NUM_PER_TYPE

positions = np.random.uniform(0, 1000, (NUM_PARTICLES, 2))
velocities = np.zeros((NUM_PARTICLES, 2))

# Create types
types = np.repeat(np.arange(NUM_TYPES), NUM_PER_TYPE)

# Interaction matrix [-1, 1]
# Positive = attract, Negative = repel
interaction = np.random.uniform(-1, 1, (NUM_TYPES, NUM_TYPES))
# Make it asymmetrical to induce motion
interaction[0,1] = 0.8
interaction[1,0] = -0.4
interaction[1,2] = 0.7
interaction[2,1] = -0.5
interaction[2,3] = 0.9
interaction[3,2] = -0.8
interaction[3,0] = 0.6
interaction[0,3] = -0.7

colors = [
    (340, 80, 100), # Pink/Red
    (180, 80, 100), # Cyan
    (60, 80, 100),  # Yellow
    (280, 80, 100)  # Purple
]

# Friction and max radius
r_max = 80.0
friction = 0.5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions
    positions[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    positions[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    
    py5.no_stroke()

def draw():
    global positions, velocities
    
    # Trails
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 10, 15, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # O(N^2) interaction using numpy broadcasting
    # To avoid memory issues with huge arrays, we'll process it efficiently
    # positions shape: (N, 2)
    # diff shape: (N, N, 2)
    
    # Actually doing N^2 distance directly for 4800 particles is 4800x4800x2 = ~46MB, which is fine
    
    pos_x = positions[:, 0:1]
    pos_y = positions[:, 1:2]
    
    dx = pos_x.T - pos_x
    dy = pos_y.T - pos_y
    
    dist_sq = dx**2 + dy**2
    # Prevent divide by zero
    dist_sq[dist_sq < 1.0] = 1.0
    dist = np.sqrt(dist_sq)
    
    # Mask within interaction radius
    mask = dist < r_max
    np.fill_diagonal(mask, False)
    
    force_x = np.zeros(NUM_PARTICLES)
    force_y = np.zeros(NUM_PARTICLES)
    
    for i in range(NUM_TYPES):
        for j in range(NUM_TYPES):
            g = interaction[i, j]
            if g != 0:
                # Mask for particles of type i and type j
                idx_i = types == i
                idx_j = types == j
                
                # Get distances and directions between type i and type j
                # We need dx[idx_i, :][:, idx_j]
                m_dx = dx[np.ix_(idx_i, idx_j)]
                m_dy = dy[np.ix_(idx_i, idx_j)]
                m_dist = dist[np.ix_(idx_i, idx_j)]
                m_mask = mask[np.ix_(idx_i, idx_j)]
                
                # Force magnitude proportional to gravity and inverse distance
                # Smooth dropoff to 0 at r_max
                f_mag = g * (1.0 - m_dist / r_max)
                f_mag = np.where(m_mask, f_mag, 0)
                
                # Add strong repulsion at very short ranges to simulate solid particles
                repulsion = np.where(m_dist < 10.0, -2.0 * (1.0 - m_dist / 10.0), 0)
                f_mag += np.where(m_mask, repulsion, 0)
                
                fx = (m_dx / m_dist) * f_mag
                fy = (m_dy / m_dist) * f_mag
                
                force_x[idx_i] += np.sum(fx, axis=1)
                force_y[idx_i] += np.sum(fy, axis=1)

    velocities[:, 0] = (velocities[:, 0] + force_x) * friction
    velocities[:, 1] = (velocities[:, 1] + force_y) * friction
    
    positions += velocities
    
    # Screen wrapping
    positions[:, 0] = positions[:, 0] % py5.width
    positions[:, 1] = positions[:, 1] % py5.height
    
    # Draw
    for i in range(NUM_TYPES):
        idx = types == i
        py5.fill(*colors[i])
        
        pos_i = positions[idx]
        
        # Use simple rects for fast drawing
        # Add a glow layer
        for r in [6, 3]:
            if r == 6:
                py5.fill(colors[i][0], colors[i][1], colors[i][2], 30)
            else:
                py5.fill(*colors[i])
                
            for p in pos_i:
                py5.rect(p[0] - r/2, p[1] - r/2, r, r)

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
