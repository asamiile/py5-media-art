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
from lib.safety import apply_anti_flicker_filter

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
    py5.color_mode(py5.RGB, 255)

def draw():
    py5.background(10)
    
            
    # Draw some base geometry
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    py5.no_fill()
    py5.stroke_weight(20)
    
    t = py5.frame_count * 0.05
    for i in range(15):
        s = 200 + i * 150
        py5.stroke(0, 255 - i*15, 200)
        py5.ellipse(0, 0, s + py5.sin(t + i)*100, s + py5.cos(t - i)*100)
    py5.pop_matrix()

    # Glitch VHS distortion effect over the image
    py5.load_np_pixels()
    
    w = py5.width
    h = py5.height
    
    # Copy pixels for manipulation
    original_pixels = np.copy(py5.np_pixels)
    
    for y in range(0, h, 4):
        # Scanline offset based on noise
        glitch_amt = py5.os_noise(y * 0.01, py5.frame_count * 0.1)
        # Create occasional severe spikes
        if random.random() < 0.02:
            glitch_amt *= 50
        else:
            glitch_amt = int(glitch_amt * 20)
            
        if abs(glitch_amt) > 0:
            # Shift the row horizontally
            row_data = original_pixels[y:y+4, :]
            shifted_row = np.roll(row_data, glitch_amt, axis=1)
            py5.np_pixels[y:y+4, :] = shifted_row
            
            # Chromatic aberration for the shifted part
            if abs(glitch_amt) > 10:
                py5.np_pixels[y:y+4, :, 0] = np.roll(shifted_row[:, :, 0], 5, axis=1) # Shift Red
                py5.np_pixels[y:y+4, :, 2] = np.roll(shifted_row[:, :, 2], -5, axis=1) # Shift Blue
                
    py5.update_np_pixels()

    apply_anti_flicker_filter(0.5)
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
