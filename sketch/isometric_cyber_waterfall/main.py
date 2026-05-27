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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle system for falling cubes
NUM_CUBES = 800
positions = None
velocities = None
lifetimes = None
colors = None

def setup():
    global positions, velocities, lifetimes, colors
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize outside screen
    positions = np.zeros((NUM_CUBES, 3))
    positions[:, 1] = -5000
    velocities = np.zeros((NUM_CUBES, 3))
    lifetimes = np.random.rand(NUM_CUBES) * 100
    
    # Deep blue to cyan
    hues = np.random.choice([0, 1], NUM_CUBES, p=[0.7, 0.3]) 
    colors = np.zeros((NUM_CUBES, 3))
    colors[hues == 0] = [0, 100, 255] # Cyan/Blue
    colors[hues == 1] = [0, 255, 255] # Cyan

def reset_cube(i):
    # Spawn at top
    positions[i, 0] = (np.random.rand() - 0.5) * 800
    positions[i, 1] = -800 - np.random.rand() * 400
    positions[i, 2] = (np.random.rand() - 0.5) * 800
    velocities[i, :] = [0, 0, 0]
    lifetimes[i] = 200 + np.random.rand() * 100

def draw():
    global positions, velocities, lifetimes
    
    py5.background(0)
    
    # Isometric camera
    py5.ortho(-SIZE[0], SIZE[0], -SIZE[1], SIZE[1], -5000, 5000)
    py5.camera(1000, -1000, 1000, 0, 0, 0, 0, 1, 0)
    
    # Lighting
    py5.directional_light(0, 255, 255, -1, 1, -1)
    py5.directional_light(0, 50, 150, 1, 1, 1)
    
    # Gravity
    velocities[:, 1] += 0.8
    
    # Update positions
    positions += velocities
    
    # Staircase collision logic
    # Stairs are defined by step width and height
    step_w = 150
    step_h = 150
    
    for i in range(NUM_CUBES):
        if lifetimes[i] <= 0 or positions[i, 1] > 1000:
            reset_cube(i)
            continue
            
        lifetimes[i] -= 1
        
        # Calculate which step we are above based on x and z
        # Simple diagonal stairs
        stair_index = np.floor((positions[i, 0] + positions[i, 2]) / step_w)
        floor_y = stair_index * step_h
        
        # Collision
        if positions[i, 1] > floor_y:
            positions[i, 1] = floor_y
            velocities[i, 1] *= -0.5 # bounce
            
            # Slide off the step
            velocities[i, 0] += (np.random.rand() - 0.2) * 2
            velocities[i, 2] += (np.random.rand() - 0.2) * 2
            
    py5.no_stroke()
    
    # Draw stairs as static boxes for context
    py5.fill(10, 10, 20)
    for i in range(-5, 6):
        py5.push_matrix()
        py5.translate(i * step_w, i * step_h + 200, i * step_w)
        py5.box(step_w * 2, 400, step_w * 2)
        py5.pop_matrix()
        
    # Draw cubes
    py5.emissive(0, 150, 255)
    for i in range(NUM_CUBES):
        if positions[i, 1] > -900:
            py5.push_matrix()
            py5.translate(positions[i, 0], positions[i, 1], positions[i, 2])
            # Rotate based on velocity
            py5.rotate_x(positions[i, 2] * 0.05)
            py5.rotate_y(positions[i, 0] * 0.05)
            
            # Fill color
            py5.fill(colors[i, 0], colors[i, 1], colors[i, 2], 200)
            
            # Smaller boxes
            scale = min(1.0, lifetimes[i] / 50.0)
            py5.box(20 * scale)
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
