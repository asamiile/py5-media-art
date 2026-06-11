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

# Aizawa Attractor parameters
a = 0.95
b = 0.7
c = 0.6
d = 3.5
e = 0.25
f = 0.1
dt = 0.01
num_points = 25000

points = np.zeros((num_points, 3), dtype=np.float32)

def setup():
    global points
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    x, y, z = 0.1, 0.0, 0.0
    
    for i in range(num_points):
        dx = (z - b) * x - d * y
        dy = d * x + (z - b) * y
        dz = c + a * z - (z**3) / 3.0 - (x**2 + y**2) * (1.0 + e * z) + f * z * (x**3)
        
        x += dx * dt
        y += dy * dt
        z += dz * dt
        
        points[i] = [x, y, z]

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0, 0, 5)  # Very dark void
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    scale_factor = SIZE[1] / 1080.0
    
    py5.rotate_x(t * py5.TWO_PI * 1.0)
    py5.rotate_y(t * py5.TWO_PI * 0.5)
    py5.rotate_z(t * py5.TWO_PI * 0.25)
    
    draw_scale = 350 * scale_factor
    
    py5.stroke_weight(3 * scale_factor)
    
    py5.begin_shape()
    
    for i in range(num_points):
        normalized_pos = i / num_points
        wave = py5.sin(normalized_pos * py5.TWO_PI * 15 - t * py5.TWO_PI * 10)
        
        alpha_val = py5.remap(wave, -1, 1, 5, 80)
        hue_val = (220 + normalized_pos * 100 + t * 360) % 360
        
        py5.stroke(hue_val, 90, 100, alpha_val)
        
        x = points[i, 0] * draw_scale
        y = points[i, 1] * draw_scale
        z = points[i, 2] * draw_scale
        
        py5.vertex(x, y, z)
        
    py5.end_shape()
    
    py5.stroke_weight(8 * scale_factor)
    py5.begin_shape(py5.POINTS)
    for i in range(0, num_points, 50):
        normalized_pos = i / num_points
        wave = py5.sin(normalized_pos * py5.TWO_PI * 15 - t * py5.TWO_PI * 10)
        if wave > 0.95:
            py5.stroke(360, 0, 100, 100)
            x = points[i, 0] * draw_scale
            y = points[i, 1] * draw_scale
            z = points[i, 2] * draw_scale
            py5.vertex(x, y, z)
    py5.end_shape()

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
