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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

COLS = 50
ROWS = 50
REST_DIST = 15.0

# Verlet integration physics arrays
# pos: [x, y, z], prev_pos: [x, y, z]
pos = np.zeros((ROWS, COLS, 3), dtype=np.float32)
prev_pos = np.zeros((ROWS, COLS, 3), dtype=np.float32)

def setup():
    global pos, prev_pos
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize cloth flat on the XY plane
    start_x = -COLS * REST_DIST / 2.0
    start_y = -ROWS * REST_DIST / 2.0
    for y in range(ROWS):
        for x in range(COLS):
            pos[y, x, 0] = start_x + x * REST_DIST
            pos[y, x, 1] = start_y + y * REST_DIST
            pos[y, x, 2] = 0.0
            
    prev_pos[:] = pos[:]

def apply_constraints():
    global pos
    # Enforce structural springs (horizontal and vertical)
    for _ in range(5): # Constraint iterations
        # Horizontal
        diff_x = pos[:, 1:] - pos[:, :-1]
        dist_x = np.linalg.norm(diff_x, axis=2, keepdims=True) + 1e-2
        force_x = diff_x * (1.0 - REST_DIST / dist_x) * 0.5
        force_x = np.clip(force_x, -5.0, 5.0) # Clamp to prevent explosion
        pos[:, 1:] -= force_x
        pos[:, :-1] += force_x
        
        # Vertical
        diff_y = pos[1:, :] - pos[:-1, :]
        dist_y = np.linalg.norm(diff_y, axis=2, keepdims=True) + 1e-2
        force_y = diff_y * (1.0 - REST_DIST / dist_y) * 0.5
        force_y = np.clip(force_y, -5.0, 5.0)
        pos[1:, :] -= force_y
        pos[:-1, :] += force_y
        
        # Pin top edge
        start_x = -COLS * REST_DIST / 2.0
        start_y = -ROWS * REST_DIST / 2.0
        for x in range(COLS):
            pos[0, x, 0] = start_x + x * REST_DIST
            pos[0, x, 1] = start_y
            pos[0, x, 2] = 0.0

def update_physics(t):
    global pos, prev_pos
    
    # Verlet integration
    velocity = (pos - prev_pos) * 0.95 # Higher dampening
    velocity = np.clip(velocity, -10.0, 10.0) # Clamp max velocity
    prev_pos[:] = pos[:]
    pos += velocity
    
    # Gravity
    pos[:, :, 1] += 0.5
    
    # Wind (using Perlin noise to make it dynamic)
    wind_force = np.zeros_like(pos)
    for y in range(ROWS):
        for x in range(COLS):
            noise_val = py5.noise(x * 0.1, y * 0.1, t * 0.5)
            # Wind pushes mainly in Z direction and slightly X
            wind_force[y, x, 2] = py5.remap(noise_val, 0, 1, -2, 10)
            wind_force[y, x, 0] = py5.remap(noise_val, 0, 1, -1, 3)
            
    pos += wind_force
    
    apply_constraints()

def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.05
    update_physics(t)
    
    py5.translate(py5.width / 2, py5.height / 2 - 200, -200)
    
    # Slowly rotate the entire scene
    py5.rotate_y(py5.sin(t * 0.1) * 0.5)
    
    # Draw the cloth using Quads
    py5.no_stroke()
    py5.begin_shape(py5.QUADS)
    for y in range(ROWS - 1):
        for x in range(COLS - 1):
            p1 = pos[y, x]
            p2 = pos[y, x+1]
            p3 = pos[y+1, x+1]
            p4 = pos[y+1, x]
            
            # Map height and time to color
            hue = (p1[2] * 0.5 + t * 10 + x * 2 + y * 2) % 360
            py5.fill(hue, 80, 100, 90)
            
            py5.vertex(p1[0], p1[1], p1[2])
            py5.vertex(p2[0], p2[1], p2[2])
            py5.vertex(p3[0], p3[1], p3[2])
            py5.vertex(p4[0], p4[1], p4[2])
    py5.end_shape()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
