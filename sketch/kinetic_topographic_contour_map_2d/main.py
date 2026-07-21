from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    py5.no_stroke()
    py5.rect_mode(py5.CENTER)

def draw():
    py5.background(30, 20, 15) # Dark charcoal brown
    
    t = py5.frame_count / TOTAL_FRAMES
    
    step = 12
    contour_levels = 15
    thickness = 0.15 # 15% of the distance between contours is drawn
    
    # Precalculate loop time to make noise loop seamlessly using a 2D circle in noise space
    noise_angle = t * py5.TWO_PI
    nx_off = np.cos(noise_angle) * 1.5
    ny_off = np.sin(noise_angle) * 1.5
    
    # We want a topography that breathes
    for x in range(0, py5.width, step):
        for y in range(0, py5.height, step):
            # 3D noise (x, y, and rotating time)
            v = py5.os_noise(x * 0.0015 + nx_off, y * 0.0015 + ny_off, t)
            
            # Scale to contour levels
            scaled = v * contour_levels
            fraction = scaled % 1.0
            
            if fraction < thickness:
                # Color based on elevation (v)
                hue = py5.remap(v, 0, 1, 10, 45) # Orange to Yellow
                py5.fill(hue, 80, 90)
                
                # Size based on how close to the center of the contour line we are
                # distance to center of line (which is fraction = thickness/2)
                dist = abs(fraction - (thickness / 2.0))
                s = py5.remap(dist, 0, thickness / 2.0, step * 1.2, step * 0.3)
                
                py5.rect(x, y, s, s)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
        import os
        os._exit(0)

py5.run_sketch()
