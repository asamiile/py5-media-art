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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters for Lissajous curves
NUM_CURVES = 150
curves = []
for i in range(NUM_CURVES):
    freq_x = random.uniform(2, 6)
    freq_y = random.uniform(2, 6)
    phase_x = random.uniform(0, np.pi * 2)
    phase_y = random.uniform(0, np.pi * 2)
    amp_x = random.uniform(300, 1500)
    amp_y = random.uniform(300, 900)
    curves.append({
        'fx': freq_x, 'fy': freq_y,
        'px': phase_x, 'py': phase_y,
        'ax': amp_x, 'ay': amp_y
    })

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(20, 20, 22)
    py5.color_mode(py5.RGB, 255)
    py5.blend_mode(py5.ADD)

def draw():
    # Very slight fade for long trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 2)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    t = py5.frame_count * 0.02
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    py5.stroke_weight(2)
    
    for i in range(NUM_CURVES):
        c = curves[i]
        
        # Calculate current position
        x1 = cx + np.sin(c['fx'] * t + c['px']) * c['ax']
        y1 = cy + np.sin(c['fy'] * t + c['py']) * c['ay']
        
        # Calculate next position for drawing a line segment
        t2 = t + 0.05
        x2 = cx + np.sin(c['fx'] * t2 + c['px']) * c['ax']
        y2 = cy + np.sin(c['fy'] * t2 + c['py']) * c['ay']
        
        # Gold/Amber color, varied slightly per curve
        r = 255
        g = 180 + np.cos(i) * 70
        b = 50 + np.sin(i*2) * 50
        
        # Alpha modulated by time
        alpha = 80 + np.sin(t * 2 + i) * 60
        
        py5.stroke(r, g, b, min(255, max(0, alpha)))
        py5.line(x1, y1, x2, y2)
        
        # Rotate phases slowly
        c['px'] += 0.005
        c['py'] += 0.007

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
