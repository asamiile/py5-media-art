from pathlib import Path
import shutil
import subprocess
import sys
import math
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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(1, 16, 21)
    
def draw():
    # Motion blur / fade
    py5.fill(1, 16, 21, 60)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # We will draw 3 separate intertwining guilloche patterns
    for pattern_idx in range(3):
        
        py5.begin_shape()
        
        # Base colors: Cyan and Chartreuse
        if pattern_idx == 0:
            py5.stroke(0, 229, 255, 180) # Cyan
        elif pattern_idx == 1:
            py5.stroke(118, 255, 3, 180) # Chartreuse
        else:
            py5.stroke(255, 255, 255, 100) # Bright White
            
        steps = 3000
        loops = 80 # Number of full revolutions for theta
        
        # Parametric parameters, driven by noise
        n1 = py5.os_noise(t * 1.5, pattern_idx * 10)
        n2 = py5.os_noise(t * 1.5 + 100, pattern_idx * 10)
        n3 = py5.os_noise(t * 1.5 + 200, pattern_idx * 10)
        
        R = 400 + 100 * n1
        r = 150 + 80 * n2
        d = 200 + 150 * n3
        
        # Second layer of complexity
        R2 = 100 + 50 * math.sin(t * math.pi * 2)
        r2 = 40 + 20 * math.cos(t * math.pi * 2 + pattern_idx)
        d2 = 80 + 30 * n1
        
        phase = t * math.pi * 2
        
        for i in range(steps):
            theta = (i / steps) * (py5.TWO_PI * loops)
            
            # Primary epitrochoid
            x1 = (R + r) * math.cos(theta + phase) + d * math.cos(((R + r) / r) * theta)
            y1 = (R + r) * math.sin(theta + phase) + d * math.sin(((R + r) / r) * theta)
            
            # Secondary hypotrochoid offset
            x2 = (R2 - r2) * math.cos(theta) + d2 * math.cos(((R2 - r2) / r2) * theta)
            y2 = (R2 - r2) * math.sin(theta) - d2 * math.sin(((R2 - r2) / r2) * theta)
            
            py5.vertex(x1 + x2, y1 + y2)
            
        py5.end_shape()
        
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
