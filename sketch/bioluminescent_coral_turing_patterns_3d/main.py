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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Generating point cloud for Turing-like structures
GRID_RES = 40
SPACING = 20
points = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Pre-generate points in a sphere volume
    for x in range(-GRID_RES, GRID_RES):
        for y in range(-GRID_RES, GRID_RES):
            for z in range(-GRID_RES, GRID_RES):
                r = np.sqrt(x**2 + y**2 + z**2)
                if r <= GRID_RES:
                    points.append(np.array([x*SPACING, y*SPACING, z*SPACING], dtype=float))

def draw():
    py5.background(5, 10, 25) # Abyssal navy
    
    py5.directional_light(0, 255, 255, 1, 1, 0)
    py5.directional_light(138, 43, 226, -1, -1, 1) # Deep violet
    py5.ambient_light(20, 20, 40)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Global slow rotation
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    t = py5.frame_count * 0.015
    
    py5.no_stroke()
    py5.sphere_detail(6)
    
    # Draw points simulating a turing pattern
    for p in points:
        # Multi-scale noise to create labyrinthine / coral structures
        n1 = py5.os_noise(p[0]*0.005, p[1]*0.005, p[2]*0.005 + t*0.5)
        n2 = py5.os_noise(p[0]*0.02, p[1]*0.02, p[2]*0.02 - t)
        
        # Combine noise to get a ridge-like threshold
        val = abs(n1 - n2)
        
        if val < 0.1: # Ridge threshold
            # Smoothly calculate size based on distance to center of ridge
            s = (0.1 - val) * 10 * SPACING * 0.8
            
            py5.push_matrix()
            
            # Add organic drift
            drift_x = py5.os_noise(p[0]*0.01 + t, p[1]*0.01, p[2]*0.01) * 20
            drift_y = py5.os_noise(p[0]*0.01, p[1]*0.01 + t, p[2]*0.01) * 20
            
            py5.translate(p[0] + drift_x, p[1] + drift_y, p[2])
            
            if val < 0.02:
                # Core bright spots (Neon green)
                py5.fill(57, 255, 20, 200)
                py5.scale(s * 1.5)
            else:
                # Main body (Cyan)
                py5.fill(0, 200, 255, 150)
                py5.scale(s)
                
            py5.box(1) # Use box instead of sphere for performance on large point clouds
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
