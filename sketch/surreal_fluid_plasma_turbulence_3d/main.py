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
DURATION_SEC = 20
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
    py5.background(0)

def draw():
    # Only partially clear background for trails
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)

    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.01

    py5.rotate_x(t * 0.5)
    py5.rotate_y(t * 0.3)
    py5.rotate_z(t * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    num_particles = 200
    py5.stroke_weight(2)
    
    for i in range(num_particles):
        x_noise = py5.os_noise(i * 0.1, t, 0) - 0.5
        y_noise = py5.os_noise(0, i * 0.1, t) - 0.5
        z_noise = py5.os_noise(t, 0, i * 0.1) - 0.5
        
        r = 500 + 300 * py5.sin(t * 2 + i * 0.05)
        
        x = x_noise * r * 2
        y = y_noise * r * 2
        z = z_noise * r * 2
        
        hue = (t * 20 + i * 2) % 360
        py5.stroke(hue, 80, 100, 50)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.box(10 + 20 * py5.os_noise(i, t))
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

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
