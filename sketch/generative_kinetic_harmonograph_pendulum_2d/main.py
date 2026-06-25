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
from lib.preview import preview_filename
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
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)

def get_harmonograph_pos(t):
    # Parametric equations for a 4-pendulum harmonograph
    A1, A2, A3, A4 = 600, 600, 600, 600
    f1, f2, f3, f4 = 2.01, 3.0, 3.0, 2.0
    p1, p2, p3, p4 = 0, np.pi/2, np.pi/4, 0
    d1, d2, d3, d4 = 0.005, 0.004, 0.003, 0.002
    
    # Increase the overall scale to fill 4K screen
    scale_factor = 1.2
    
    x = A1 * np.sin(t * f1 + p1) * np.exp(-d1 * t) + A2 * np.sin(t * f2 + p2) * np.exp(-d2 * t)
    y = A3 * np.sin(t * f3 + p3) * np.exp(-d3 * t) + A4 * np.sin(t * f4 + p4) * np.exp(-d4 * t)
    
    return x * scale_factor, y * scale_factor

def draw():
    # Draw slightly faded background to create trail
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 5) # Very slow fade
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # We draw multiple segments per frame to speed up the drawing process
    # so it finishes a complex shape in 15 seconds.
    t_start = (py5.frame_count - 1) * 0.1
    t_end = py5.frame_count * 0.1
    
    steps = 100
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    # Color mapping: ruby to gold over time
    hue = py5.remap(py5.frame_count, 1, TOTAL_FRAMES, 340, 50)
    hue = hue % 360
    
    py5.stroke(hue, 90, 90, 80)
    
    py5.begin_shape()
    for i in range(steps + 1):
        t = py5.lerp(t_start, t_end, i / steps)
        x, y = get_harmonograph_pos(t)
        py5.vertex(x, y)
    py5.end_shape()
    
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
