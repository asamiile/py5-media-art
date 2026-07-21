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
    py5.blend_mode(py5.ADD)

def draw():
    py5.background(0) # Black background
    t = py5.frame_count / TOTAL_FRAMES
    
    # Draw waves
    py5.no_fill()
    py5.stroke_weight(25)
    
    # Red wave
    py5.stroke(0, 100, 100)
    draw_wave(t, offset=0.0)
    
    # Green wave
    py5.stroke(120, 100, 100)
    draw_wave(t, offset=0.02)
    
    # Blue wave
    py5.stroke(240, 100, 100)
    draw_wave(t, offset=0.04)

    # Glitch effect (horizontal slices)
    if py5.os_noise(t * 15.0, 0.0) > 0.65:
        # Load pixels and slice them
        py5.load_np_pixels()
        pixels = py5.np_pixels.copy()
        
        num_slices = random.randint(10, 30)
        slice_height = py5.height // num_slices
        
        for i in range(num_slices):
            if random.random() > 0.5:
                shift_x = random.randint(-150, 150)
                y_start = i * slice_height
                y_end = (i + 1) * slice_height
                
                # Roll pixels horizontally
                pixels[y_start:y_end] = np.roll(pixels[y_start:y_end], shift_x, axis=1)
                
        py5.np_pixels[:] = pixels
        py5.update_np_pixels()

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

def draw_wave(t, offset):
    py5.begin_shape()
    for x in range(-100, py5.width + 100, 20):
        y = py5.height / 2 + np.sin((x / 500.0) + (t + offset) * py5.TWO_PI * 4) * 300
        # Add noise
        y += py5.os_noise(x * 0.01, (t + offset) * 2.0) * 200 - 100
        py5.vertex(x, y)
    py5.end_shape()

py5.run_sketch()
