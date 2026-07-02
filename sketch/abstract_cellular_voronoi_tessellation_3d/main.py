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

# Voronoi seeds
num_seeds = 15
seeds = np.zeros((num_seeds, 2), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize random starting positions for seeds
    for i in range(num_seeds):
        seeds[i, 0] = py5.random(0, SIZE[0])
        seeds[i, 1] = py5.random(0, SIZE[1])

def draw():
    py5.background(20, 10, 5) # Dark space
    
    time = py5.frame_count * 0.01
    
    py5.directional_light(320, 50, 100, 1, 1, -1)
    py5.directional_light(180, 50, 100, -1, -1, -0.5)
    py5.ambient_light(0, 0, 20)
    
    # Update seed positions with noise
    for i in range(num_seeds):
        seeds[i, 0] += (py5.os_noise(i * 10, time) - 0.5) * 10
        seeds[i, 1] += (py5.os_noise(i * 10 + 100, time) - 0.5) * 10
        
        # Wrap
        if seeds[i, 0] < -500: seeds[i, 0] = SIZE[0] + 500
        if seeds[i, 0] > SIZE[0] + 500: seeds[i, 0] = -500
        if seeds[i, 1] < -500: seeds[i, 1] = SIZE[1] + 500
        if seeds[i, 1] > SIZE[1] + 500: seeds[i, 1] = -500
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -300)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(time * 0.2)
    
    py5.translate(-SIZE[0], -SIZE[1], 0)
    
    cols = 60
    rows = 60
    scl = SIZE[0]*2 / cols
    
    py5.no_stroke()
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            
            # Helper to calculate Voronoi Z and color
            def get_v_data(px, py):
                min_d = 999999
                closest_i = 0
                for i in range(num_seeds):
                    d = (px - seeds[i, 0])**2 + (py - seeds[i, 1])**2
                    if d < min_d:
                        min_d = d
                        closest_i = i
                
                # Z height based on distance
                z = py5.sqrt(min_d) * 0.8
                # Invert so seeds are peaks
                z = 500 - z
                if z < 0: z = 0
                
                return z, closest_i
            
            px1 = x * scl
            py1 = y * scl
            z1, c1 = get_v_data(px1, py1)
            
            px2 = x * scl
            py2 = (y + 1) * scl
            z2, c2 = get_v_data(px2, py2)
            
            # Fill color based on closest seed
            hue1 = (c1 * 40 + time * 10) % 360
            py5.fill(hue1, 80, 100)
            py5.vertex(px1, py1, z1)
            
            hue2 = (c2 * 40 + time * 10) % 360
            py5.fill(hue2, 80, 100)
            py5.vertex(px2, py2, z2)
            
        py5.end_shape()

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
