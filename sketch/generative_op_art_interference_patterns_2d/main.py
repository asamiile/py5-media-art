from pathlib import Path
import shutil
import subprocess
import sys
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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw():
    py5.background(0, 0, 100) # White background
    
    time = py5.frame_count * 0.02
    
    # Base layer: static concentric circles
    py5.no_fill()
    py5.stroke(0, 0, 0)
    py5.stroke_weight(12)
    
    cx = SIZE[0] / 2
    cy = SIZE[1] / 2
    
    for r in range(50, 4000, 40):
        py5.ellipse(cx, cy, r, r)
        
    # Top layer: moving concentric circles to create moire
    offset_x = py5.sin(time * 0.5) * 300
    offset_y = py5.cos(time * 0.4) * 300
    
    # We can use DIFFERENCE blend mode to invert overlapping lines
    py5.blend_mode(py5.DIFFERENCE)
    
    py5.stroke(0, 0, 100) # Draw white lines in difference mode -> inverts black
    py5.stroke_weight(14)
    
    for r in range(50, 4000, 42):
        py5.ellipse(cx + offset_x, cy + offset_y, r, r)
        
    # Add radial lines
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(time * 0.1)
    py5.stroke_weight(8)
    for i in range(120):
        angle = i * py5.TWO_PI / 120
        x1 = py5.cos(angle) * 100
        y1 = py5.sin(angle) * 100
        x2 = py5.cos(angle) * 4000
        y2 = py5.sin(angle) * 4000
        py5.line(x1, y1, x2, y2)
    py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

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
