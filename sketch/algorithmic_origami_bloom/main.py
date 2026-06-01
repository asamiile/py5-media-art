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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw_petal(depth, max_depth, t):
    if depth == 0:
        return
        
    length = py5.width * 0.1 * (0.85 ** (max_depth - depth))
    
    # Oscillation angles
    angle_x = py5.sin(t * py5.TWO_PI + depth * 0.5) * py5.PI / 4
    angle_y = py5.cos(t * py5.TWO_PI + depth * 0.3) * py5.PI / 4
    
    py5.push_matrix()
    
    py5.rotate_x(angle_x)
    py5.rotate_y(angle_y)
    
    # Rose Gold to Indigo to White gradient
    hue = (345 + depth * 15 + t * 360) % 360
    py5.fill(hue, 60, 90, 180)
    py5.stroke(0, 0, 100, 200)
    py5.stroke_weight(3)
    
    py5.begin_shape(py5.TRIANGLES)
    py5.vertex(0, 0, 0)
    py5.vertex(-length/2, -length, length/4)
    py5.vertex(length/2, -length, length/4)
    py5.end_shape()
    
    py5.translate(0, -length, length/4)
    
    # Branching
    for i in range(2):
        py5.push_matrix()
        py5.rotate_z(py5.PI/4 if i == 0 else -py5.PI/4)
        draw_petal(depth - 1, max_depth, t)
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    py5.background(0)
    
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 0, 1, -1)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Global rotation
    py5.rotate_y(t * py5.TWO_PI * 2)
    py5.rotate_x(py5.PI / 4)
    py5.rotate_z(py5.sin(t * py5.TWO_PI) * py5.PI / 8)
    
    num_petals = 6
    for i in range(num_petals):
        py5.push_matrix()
        py5.rotate_z(i * py5.TWO_PI / num_petals)
        draw_petal(5, 5, t)
        py5.pop_matrix()
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.", flush=True)
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.", flush=True)
            
        import os
        os._exit(0)

py5.run_sketch()
