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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols, rows = 30, 40
size = 60
w = cols * size * 1.5
h = rows * size * np.sqrt(3)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(220, 90, 5)
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    # Camera movement
    cam_angle = py5.frame_count * 0.005
    py5.rotate_x(py5.PI / 3 + np.sin(cam_angle) * 0.2)
    py5.rotate_z(cam_angle * 1.5)
    
    py5.translate(-w / 2, -h / 2, 0)
    
    py5.stroke_weight(2)
    py5.stroke(200, 50, 100, 80)
    
    t = py5.frame_count * 0.03
    
    # Draw triangular tessellation
    for y in range(rows):
        for x in range(cols):
            x_pos = x * size * 1.5
            y_pos = y * size * np.sqrt(3)
            
            # Offset every other row
            if x % 2 == 1:
                y_pos += size * np.sqrt(3) / 2
                
            # Distance from center for radial ripple
            cx = x_pos - w / 2
            cy = y_pos - h / 2
            dist = np.sqrt(cx*cx + cy*cy)
            
            # Angle for folding
            noise_val = py5.os_noise(x * 0.1, y * 0.1, t * 0.5)
            ripple = np.sin(dist * 0.01 - t * 2) * 1.5
            fold_angle = py5.remap(noise_val, -1, 1, 0, py5.PI) + ripple
            
            hue = (200 + noise_val * 60 + dist * 0.05 + py5.frame_count) % 360
            bright = py5.remap(np.cos(fold_angle), -1, 1, 30, 100)
            
            py5.push_matrix()
            py5.translate(x_pos, y_pos, 0)
            
            py5.fill(hue, 80, bright, 90)
            
            # Triangle 1
            py5.push_matrix()
            py5.rotate_x(fold_angle)
            py5.begin_shape(py5.TRIANGLES)
            py5.vertex(0, -size, 0)
            py5.vertex(size * 0.866, size * 0.5, 0)
            py5.vertex(-size * 0.866, size * 0.5, 0)
            py5.end_shape()
            py5.pop_matrix()
            
            # Triangle 2 (inverted)
            if x < cols - 1:
                py5.fill((hue + 20) % 360, 80, bright * 0.8, 90)
                py5.push_matrix()
                py5.translate(size * 1.5, size * np.sqrt(3) / 2, 0) if x % 2 == 0 else py5.translate(size * 1.5, -size * np.sqrt(3) / 2, 0)
                py5.rotate_y(fold_angle * 1.2)
                py5.begin_shape(py5.TRIANGLES)
                py5.vertex(0, size, 0)
                py5.vertex(-size * 0.866, -size * 0.5, 0)
                py5.vertex(size * 0.866, -size * 0.5, 0)
                py5.end_shape()
                py5.pop_matrix()
            
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
