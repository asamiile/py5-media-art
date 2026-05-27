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

cols = 0
rows = 0
scl = 100
w = 3000
h = 3000

def setup():
    global cols, rows
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cols = w // scl
    rows = h // scl

def draw():
    py5.background(0)
    
    # Lighting
    py5.directional_light(200, 100, 100, 0, 1, -1) # Teal
    py5.directional_light(280, 100, 100, -1, 0, -0.5) # Violet
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -800)
    py5.rotate_x(py5.PI / 3)
    
    time = py5.frame_count * 0.05
    
    py5.translate(-w/2, -h/2)
    
    py5.no_stroke()
    
    for y in range(rows):
        for x in range(cols):
            # Calculate distance from center
            dist = np.sqrt((x - cols/2)**2 + (y - rows/2)**2)
            
            # Combine wave and noise
            wave = np.sin(dist * 0.2 - time * 1.5)
            noise_val = py5.os_noise(x * 0.05 + time * 0.2, y * 0.05 - time * 0.1)
            
            # Scale factor
            scale_fac = py5.remap(wave + noise_val, -1, 2, 0.1, 1.2)
            scale_fac = max(0.1, scale_fac)
            
            # Rotation
            rot_z = wave * py5.PI + time
            
            # Color based on scale and distance
            hue = (180 + dist * 5 + noise_val * 60 + time * 5) % 360
            # Constrain to teal/violet
            if hue > 300: hue = 300
            if hue < 180: hue = 180
            
            py5.push_matrix()
            py5.translate(x * scl + scl/2, y * scl + scl/2, 0)
            py5.rotate_z(rot_z)
            py5.rotate_x(wave * py5.PI/2)
            py5.scale(scale_fac)
            
            py5.fill(hue, 90, 100)
            py5.box(scl * 0.8)
            
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
