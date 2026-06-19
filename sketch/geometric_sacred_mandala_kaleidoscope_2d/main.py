from pathlib import Path
import shutil
import subprocess
import sys
import random
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
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(10)
    py5.no_fill()

def draw_mandala_layer(radius, sides, time_t, hue_base):
    py5.stroke(hue_base % 360, 80, 100, 150)
    py5.stroke_weight(2)
    
    angle_step = py5.TWO_PI / sides
    
    for i in range(sides):
        py5.push_matrix()
        py5.rotate(i * angle_step + time_t * 0.1)
        
        # Draw interlocking geometry
        py5.begin_shape()
        for j in range(3):
            r = radius * (1.0 + 0.3 * np.sin(time_t * 2.0 + j))
            a = j * py5.TWO_PI / 3
            py5.vertex(np.cos(a) * r, np.sin(a) * r)
        py5.end_shape(py5.CLOSE)
        
        # Connecting lines
        py5.line(radius, 0, radius * 1.5 * np.cos(time_t), radius * 1.5 * np.sin(time_t))
        
        py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10) # Trail effect
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    num_layers = 12
    base_hue = time_t * 10
    
    for layer in range(num_layers, 0, -1):
        radius = layer * 40 + np.sin(time_t + layer * 0.5) * 20
        sides = 6 + layer * 2
        
        py5.push_matrix()
        py5.rotate(time_t * 0.05 * (1 if layer % 2 == 0 else -1))
        draw_mandala_layer(radius, sides, time_t, base_hue + layer * 30)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
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
