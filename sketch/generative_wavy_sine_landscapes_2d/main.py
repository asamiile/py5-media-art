from pathlib import Path
import shutil
import subprocess
import sys
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
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()

def draw():
    # Gradient background
    for y in range(0, py5.height, 20):
        py5.fill(280, 80, py5.remap(y, 0, py5.height, 10, 40))
        py5.rect(0, y, py5.width, 20)

    t = py5.frame_count * 0.015
    
    num_layers = 25
    y_step = py5.height / num_layers
    
    for i in range(num_layers):
        base_y = py5.height * 0.15 + i * y_step
        
        # Color mapped by depth
        hue = (180 + i * 5 - py5.frame_count * 0.2) % 360
        sat = 80
        bri = py5.remap(i, 0, num_layers - 1, 20, 100)
        
        py5.fill(hue, sat, bri, 240)
        
        py5.begin_shape()
        py5.vertex(0, py5.height)
        
        # Draw wave curve
        for x in range(0, py5.width + 100, 100):
            # Noise-driven terrain
            noise_val = py5.os_noise(x * 0.002, i * 0.1, t)
            
            # Additional sine wave for rhythm
            sine_val = py5.sin(x * 0.005 + t * 2 + i) * 50
            
            y_offset = py5.remap(noise_val, 0, 1, -150, 150) + sine_val
            
            # Parallax scrolling
            px = x - (py5.frame_count * py5.remap(i, 0, num_layers-1, 1, 5)) % 100
            
            if px < 0:
                px = 0
            
            py5.vertex(px, base_y + y_offset)
            
        py5.vertex(py5.width, py5.height)
        py5.end_shape(py5.CLOSE)

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
