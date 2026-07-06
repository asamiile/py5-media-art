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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 20, 30)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 20, 30, 25)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    # Parameters for Lissajous
    A = SIZE[0] * 0.4
    B = SIZE[1] * 0.4
    
    # Base frequencies that slowly change
    a1 = 3.0 + np.sin(t * 0.7) * 1.5
    b1 = 2.0 + np.cos(t * 0.5) * 1.0
    d1 = t * 2.0
    
    a2 = 4.0 + np.cos(t * 1.1) * 2.0
    b2 = 5.0 + np.sin(t * 0.8) * 1.5
    d2 = t * 3.0
    
    py5.blend_mode(py5.ADD)
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # Draw a complex ribbon of Lissajous curves
    num_steps = 400
    for i in range(num_steps):
        # We sample points along the curve
        pt = i * 0.02
        
        # Color gradient along the curve
        c_phase = t + pt * 0.5
        r = int(100 + np.sin(c_phase) * 100)
        g = int(100 + np.sin(c_phase + 2) * 100)
        b = int(150 + np.sin(c_phase + 4) * 100)
        py5.stroke(r, g, b, 40)
        
        x1 = A * np.sin(a1 * pt + d1)
        y1 = B * np.sin(b1 * pt)
        
        x2 = A * np.sin(a2 * pt + d2)
        y2 = B * np.sin(b2 * pt)
        
        # Connect points from two different curves
        py5.line(x1, y1, x2, y2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
