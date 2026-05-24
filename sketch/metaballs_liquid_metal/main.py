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

# Render at half resolution for performance, upscale later
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2

NUM_BALLS = 30
balls_pos = np.random.rand(NUM_BALLS, 2).astype(np.float32)
balls_pos[:, 0] *= SIM_W
balls_pos[:, 1] *= SIM_H

balls_vel = (np.random.rand(NUM_BALLS, 2).astype(np.float32) - 0.5) * 6.0
balls_radius = np.random.uniform(20.0, 60.0, NUM_BALLS).astype(np.float32)
balls_r2 = balls_radius ** 2

# Coordinate grid
x_range = np.arange(SIM_W, dtype=np.float32)
y_range = np.arange(SIM_H, dtype=np.float32)
xv, yv = np.meshgrid(x_range, y_range)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global balls_pos, balls_vel
    
    # Update positions
    balls_pos += balls_vel
    
    # Bounce off edges
    for i in range(NUM_BALLS):
        if balls_pos[i, 0] < 0 or balls_pos[i, 0] >= SIM_W:
            balls_vel[i, 0] *= -1
            balls_pos[i, 0] = np.clip(balls_pos[i, 0], 0, SIM_W - 1)
        if balls_pos[i, 1] < 0 or balls_pos[i, 1] >= SIM_H:
            balls_vel[i, 1] *= -1
            balls_pos[i, 1] = np.clip(balls_pos[i, 1], 0, SIM_H - 1)
            
    # Compute metaball implicit function: Sum( r^2 / d^2 )
    # To avoid division by zero, add a small epsilon
    field = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    
    for i in range(NUM_BALLS):
        dx = xv - balls_pos[i, 0]
        dy = yv - balls_pos[i, 1]
        dist_sq = dx**2 + dy**2 + 1e-4
        field += balls_r2[i] / dist_sq
        
    # Map the scalar field to a metallic color palette using periodic functions (sine)
    # This creates the illusion of metallic reflection bands
    
    # Base metallic grey/silver
    r = np.sin(field * 5.0) * 127 + 128
    g = np.sin(field * 5.0 + 0.5) * 127 + 128
    b = np.sin(field * 5.0 + 1.0) * 127 + 128
    
    # Sharp threshold mask for the outer boundary
    mask = (field > 0.8).astype(np.float32)
    
    r = (r * mask).astype(np.uint8)
    g = (g * mask).astype(np.uint8)
    b = ((b * 0.8 + 50) * mask).astype(np.uint8) # Slight blue tint to the metal
    
    # Upscale 2x
    r_up = np.kron(r, np.ones((2, 2), dtype=np.uint8))
    g_up = np.kron(g, np.ones((2, 2), dtype=np.uint8))
    b_up = np.kron(b, np.ones((2, 2), dtype=np.uint8))
    
    r_up = r_up[:SIZE[1], :SIZE[0]]
    g_up = g_up[:SIZE[1], :SIZE[0]]
    b_up = b_up[:SIZE[1], :SIZE[0]]
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = r_up
    pixels[:, :, 2] = g_up
    pixels[:, :, 3] = b_up
    
    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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
