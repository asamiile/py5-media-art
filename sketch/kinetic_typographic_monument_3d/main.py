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

GRID_W, GRID_H = 60, 40
SPACING = 30
font = None

def setup():
    global font
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create a font for the typography
    font = py5.create_font("Courier New", 24)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)
    
def draw():
    py5.background(10, 10, 15) # Very dark blue/black
    
    py5.ambient_light(50, 50, 60)
    py5.directional_light(200, 220, 255, 0.5, 1, -1) # Silver light
    py5.point_light(0, 100, 255, py5.width/2, py5.height, 200) # Deep Ocean Blue from below
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Dynamic camera orbit
    py5.rotate_x(np.pi/3 + np.sin(py5.frame_count * 0.01) * 0.15)
    py5.rotate_z(py5.frame_count * 0.003)
    
    offset_x = (GRID_W - 1) * SPACING / 2
    offset_y = (GRID_H - 1) * SPACING / 2
    
    py5.translate(-offset_x, -offset_y, 0)
    
    t = py5.frame_count * 0.02
    
    for x in range(GRID_W):
        for y in range(GRID_H):
            # Noise-based displacement
            n1 = py5.os_noise(x * 0.05, y * 0.05, t)
            n2 = py5.os_noise(x * 0.1, y * 0.1, t + 100)
            
            z = (n1 - 0.5) * 400
            
            rot_x = n2 * py5.TWO_PI
            rot_y = n1 * py5.TWO_PI
            
            py5.push_matrix()
            py5.translate(x * SPACING, y * SPACING, z)
            
            # Rotation
            py5.rotate_x(rot_x)
            py5.rotate_y(rot_y)
            
            # Character selection
            char = "1" if (x + y + int(t*10)) % 2 == 0 else "0"
            
            # Occasional glitch
            is_glitch = py5.random(1) < 0.01
            if is_glitch:
                char = py5.random_choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ@#%&*"))
                py5.fill(0, 255, 100) # Phosphor Green
                py5.scale(1.5)
            else:
                # Brushed Aluminum / Silver
                val = int(150 + 105 * n1)
                py5.fill(val, val, val + 10)
                
            py5.text(char, 0, 0)
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
