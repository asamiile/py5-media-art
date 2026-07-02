from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
GRID_SIZE = 40
CELL_SIZE = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(240, 240, 235)  # Warm minimalist concrete gray/off-white
    
    # Orthographic camera for isometric look
    py5.ortho(-py5.width/2, py5.width/2, -py5.height/2, py5.height/2, -10000, 10000)
    
    # Isometric camera positioning
    py5.camera(2000, 2000, 2000, 0, 0, 0, 0, 1, 0)
    
    # Lighting for harsh shadows
    py5.ambient_light(80, 80, 90)
    py5.directional_light(255, 245, 230, -1, 1, -1)
    py5.directional_light(100, 110, 120, 1, -0.5, 1)
    
    py5.no_stroke()
    
    time_val = py5.frame_count * 0.015
    
    # Draw the maze
    offset = (GRID_SIZE * CELL_SIZE) / 2
    
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            # Perlin noise driving the height
            noise_val = py5.os_noise(x * 0.08, z * 0.08, time_val)
            
            # Create a labyrinth pattern using sine waves mixed with noise
            wave = py5.sin((x + z) * 0.5 + time_val * 2) * py5.cos((x - z) * 0.5 + time_val)
            
            # Threshold to make sharp walls
            if noise_val + wave * 0.2 > 0.1:
                target_height = py5.remap(noise_val, 0.1, 1.0, 50, 400)
            else:
                target_height = 10  # Ground level
                
            py5.push_matrix()
            
            px = x * CELL_SIZE - offset
            pz = z * CELL_SIZE - offset
            
            py5.translate(px, target_height / 2, pz)
            
            # Color assignment based on height to give subtle depth
            c_val = py5.remap(target_height, 10, 400, 200, 255)
            py5.fill(c_val, c_val * 0.98, c_val * 0.95)
            
            py5.box(CELL_SIZE - 2, target_height, CELL_SIZE - 2)
            
            py5.pop_matrix()
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
