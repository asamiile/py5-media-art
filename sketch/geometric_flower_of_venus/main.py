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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# History of lines to draw (we draw them cumulatively to form the mandala)
history = []
MAX_HISTORY = 3000

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10)
    
def draw():
    # We don't clear the background entirely. We let the lines accumulate.
    # But we do a very faint fade to create a glowing effect.
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 2)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # We will simulate multiple "days" per frame to draw the flower faster
    steps_per_frame = 5
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    for step in range(steps_per_frame):
        # Global time for the simulation
        t = (py5.frame_count * steps_per_frame + step) * 0.015
        
        # Orbital parameters (Radius and speed/resonance ratio)
        # Earth is 8 years, Venus is 13 years for the classic 5-petal flower (8:13 resonance).
        # We use a 7:12 resonance or smoothly morphing ratios for dynamic art.
        
        ratio1 = 7.0 + py5.sin(t * 0.01) * 0.5
        ratio2 = 12.0 + py5.cos(t * 0.015) * 0.5
        
        r1 = py5.remap(py5.sin(t * 0.1), -1, 1, 200, 450)
        r2 = py5.remap(py5.cos(t * 0.1), -1, 1, 200, 450)
        
        # Calculate positions
        x1 = r1 * py5.cos(t * ratio1)
        y1 = r1 * py5.sin(t * ratio1)
        
        x2 = r2 * py5.cos(t * ratio2)
        y2 = r2 * py5.sin(t * ratio2)
        
        # Calculate a third planet for extra complexity
        ratio3 = 3.0
        r3 = 100
        x3 = r3 * py5.cos(-t * ratio3)
        y3 = r3 * py5.sin(-t * ratio3)
        
        # Draw the lines
        hue1 = (t * 20) % 360
        hue2 = (t * 20 + 180) % 360
        
        py5.stroke_weight(1)
        
        py5.stroke(hue1, 80, 100, 15)
        py5.line(x1, y1, x2, y2)
        
        py5.stroke(hue2, 80, 100, 15)
        py5.line(x2, y2, x3, y3)
        
        # Draw the planets (just glowing dots at the current position)
        py5.no_stroke()
        py5.fill(hue1, 50, 100, 50)
        py5.circle(x1, y1, 4)
        py5.circle(x2, y2, 4)
        py5.circle(x3, y3, 4)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
