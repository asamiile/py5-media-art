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

# Magnetic pendulum physics constants
NUM_PENDULUMS = 200
# State: [x, y, vx, vy]
state = np.zeros((NUM_PENDULUMS, 4), dtype=np.float32)

# Start positions: a grid or circle of slightly different initial points
angles = np.linspace(0, 2*np.pi, NUM_PENDULUMS, endpoint=False)
radii = np.random.uniform(100, 400, NUM_PENDULUMS)
state[:, 0] = np.cos(angles) * radii
state[:, 1] = np.sin(angles) * radii

# Magnets
num_magnets = 4
magnet_angles = np.linspace(0, 2*np.pi, num_magnets, endpoint=False)
magnet_radius = 250.0
magnets = np.column_stack((
    np.cos(magnet_angles) * magnet_radius,
    np.sin(magnet_angles) * magnet_radius
))

# Colors for magnets
magnet_hues = [0, 90, 180, 270] # Red, Green, Cyan, Purple

friction = 0.015
gravity_strength = 0.05
magnetic_strength = 20000.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(1.5)
    py5.blend_mode(py5.ADD)

def draw():
    global state
    
    # Motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 10, 8) # Long trails
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    dt = 0.1
    # Run multiple physics steps per frame for smooth long trails
    steps = 4
    
    for _ in range(steps):
        # Calculate forces
        # 1. Gravity towards origin
        r2 = state[:, 0]**2 + state[:, 1]**2
        
        fx = -gravity_strength * state[:, 0]
        fy = -gravity_strength * state[:, 1]
        
        # 2. Magnetic forces
        dominant_magnet = np.zeros(NUM_PENDULUMS, dtype=np.int32)
        min_dist = np.full(NUM_PENDULUMS, np.inf)
        
        for m_idx in range(num_magnets):
            dx = magnets[m_idx, 0] - state[:, 0]
            dy = magnets[m_idx, 1] - state[:, 1]
            dist_sq = dx**2 + dy**2
            
            # Avoid singularity
            dist_sq[dist_sq < 100] = 100
            
            dist = np.sqrt(dist_sq)
            
            # Force ~ 1/d^2 or 1/d^3 depending on dipole model. We use 1/d^3 here for snappy behavior
            force = magnetic_strength / (dist_sq * dist)
            fx += force * dx
            fy += force * dy
            
            # Track closest magnet for coloring
            mask = dist < min_dist
            min_dist[mask] = dist[mask]
            dominant_magnet[mask] = m_idx
            
        # 3. Friction
        fx -= friction * state[:, 2]
        fy -= friction * state[:, 3]
        
        # Update state
        new_vx = state[:, 2] + fx * dt
        new_vy = state[:, 3] + fy * dt
        
        new_x = state[:, 0] + new_vx * dt
        new_y = state[:, 1] + new_vy * dt
        
        # Draw step
        py5.push_matrix()
        py5.translate(py5.width/2, py5.height/2)
        
        # We can draw lines from old to new position
        for i in range(NUM_PENDULUMS):
            h = magnet_hues[dominant_magnet[i]]
            # Brightness based on speed
            speed = np.sqrt(new_vx[i]**2 + new_vy[i]**2)
            alpha = min(90, speed * 2 + 10)
            
            py5.stroke(h, 80, 90, alpha)
            py5.line(state[i, 0], state[i, 1], new_x[i], new_y[i])
            
        py5.pop_matrix()
        
        # Save new state
        state[:, 0] = new_x
        state[:, 1] = new_y
        state[:, 2] = new_vx
        state[:, 3] = new_vy

    # Draw magnets
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    py5.no_stroke()
    for m_idx in range(num_magnets):
        py5.fill(magnet_hues[m_idx], 80, 100, 50)
        py5.ellipse(magnets[m_idx, 0], magnets[m_idx, 1], 15, 15)
    py5.pop_matrix()

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
