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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_fill()
    py5.blend_mode(py5.ADD)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(240, 60, 5)  # Very dark indigo background
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    scale_factor = SIZE[1] / 1080.0
    
    py5.rotate_x(t * py5.TWO_PI * 0.8)
    py5.rotate_y(t * py5.TWO_PI * 0.4)
    py5.rotate_z(t * py5.TWO_PI * 0.2)
    
    num_layers = 16
    for i in range(num_layers):
        py5.push_matrix()
        
        dir_mod = 1 if i % 2 == 0 else -1
        py5.rotate_x(t * py5.TWO_PI * dir_mod * (0.2 + i * 0.05))
        py5.rotate_y(t * py5.TWO_PI * -dir_mod * (0.3 + i * 0.05))
        
        R = 250 * scale_factor + i * 40 * scale_factor
        r = 95 * scale_factor + i * 12 * scale_factor
        d = 140 * scale_factor + py5.sin(t * py5.TWO_PI * 3 + i) * 60 * scale_factor
        
        hue = (270 + i * 15 + t * 360) % 360
        py5.stroke(hue, 95, 90, 45)
        py5.stroke_weight(2 * scale_factor)
        
        py5.begin_shape()
        num_points = 1200
        for p in range(num_points):
            theta = (p / num_points) * (py5.TWO_PI * 32)
            x = (R - r) * py5.cos(theta) + d * py5.cos((R - r) / r * theta)
            y = (R - r) * py5.sin(theta) - d * py5.sin((R - r) / r * theta)
            z = py5.sin(theta * 4 + t * py5.TWO_PI) * 180 * scale_factor
            
            py5.vertex(x, y, z)
        py5.end_shape()
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
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
