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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    # Remove P3D to avoid crash on macOS headless
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    py5.rect_mode(py5.CENTER)

def draw():
    # Adding a slight fade instead of hard background
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)
    py5.rect(py5.width/2, py5.height/2, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    t = py5.frame_count * 0.01
    
    # 2D Grid simulation of polarized liquid crystals
    cols = 80
    rows = 45
    w = py5.width / cols
    h = py5.height / rows
    
    py5.translate(w/2, h/2)
    
    for i in range(cols):
        for j in range(rows):
            x = i * w
            y = j * h
            
            # Complex noise field to simulate birefringence phase shift
            n1 = py5.os_noise(i * 0.05, j * 0.05, t)
            n2 = py5.os_noise(i * 0.02 + t, j * 0.02, t * 0.5)
            
            # Interference calculation
            interference = np.sin(n1 * 10 + n2 * 5)
            
            hue = (interference * 180 + t * 50) % 360
            brightness = 40 + 60 * np.cos(interference * 3)
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(n1 * py5.TWO_PI)
            
            py5.fill(hue, 90, brightness, 100)
            
            width_mod = w * (0.5 + 1.5 * n2)
            height_mod = h * 0.2
            
            py5.rect(0, 0, width_mod, height_mod)
            py5.pop_matrix()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
