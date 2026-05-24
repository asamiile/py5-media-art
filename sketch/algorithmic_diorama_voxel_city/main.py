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

GRID_SIZE = 30
BLOCK_SIZE = 40
GRID_OFFSET = (GRID_SIZE * BLOCK_SIZE) / 2

heights = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
colors = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate the city using Perlin noise
    py5.noise_seed(42)
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            # Center of the city is taller
            dx = x - GRID_SIZE / 2
            dz = z - GRID_SIZE / 2
            dist_from_center = np.sqrt(dx**2 + dz**2)
            
            # Base height from noise
            n = py5.noise(x * 0.1, z * 0.1)
            
            # Island effect (taller in middle, dropping off at edges)
            envelope = py5.remap(dist_from_center, 0, GRID_SIZE/1.5, 1, 0)
            envelope = max(0, envelope)
            
            h = n * 400 * envelope + py5.random(10, 50)
            
            # Quantize heights for a "blocky" voxel feel
            heights[x, z] = (h // 20) * 20
            
            # Color is based on height and position
            colors[x, z] = py5.remap(heights[x, z], 0, 400, 200, 320) % 360

def draw():
    py5.background(15)
    
    t = py5.frame_count * 0.01
    
    # Position camera for an isometric-style diorama view
    py5.translate(py5.width / 2, py5.height / 2 + 200, -500)
    py5.rotate_x(py5.PI / 4)
    py5.rotate_y(py5.PI / 4 + t * 0.5)
    
    # Lighting setup
    py5.ambient_light(40, 40, 40)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(220, 80, 80, -1, 0.5, -1)
    
    py5.no_stroke()
    
    # Draw the floating island base
    py5.push_matrix()
    py5.translate(0, 20, 0)
    py5.fill(220, 80, 20)
    py5.box(GRID_SIZE * BLOCK_SIZE, 40, GRID_SIZE * BLOCK_SIZE)
    py5.pop_matrix()
    
    # Draw the buildings
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            h = heights[x, z]
            if h <= 0:
                continue
                
            px = x * BLOCK_SIZE - GRID_OFFSET + BLOCK_SIZE / 2
            pz = z * BLOCK_SIZE - GRID_OFFSET + BLOCK_SIZE / 2
            
            # Buildings subtly pulse/bob based on noise over time
            bob = py5.noise(x * 0.2, z * 0.2, t) * 30 - 15
            current_h = max(10, h + bob)
            
            py5.push_matrix()
            py5.translate(px, -current_h / 2, pz)
            
            # Occasional glowing windows
            if py5.noise(x * 5, z * 5, t * 5) > 0.8:
                py5.fill(colors[x, z], 80, 100)
                py5.emissive(colors[x, z], 100, 100)
            else:
                py5.fill(colors[x, z], 60, 80)
                py5.emissive(0, 0, 0)
                
            py5.box(BLOCK_SIZE * 0.8, current_h, BLOCK_SIZE * 0.8)
            py5.pop_matrix()

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
