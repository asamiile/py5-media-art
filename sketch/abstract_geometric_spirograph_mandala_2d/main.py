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
    py5.background(10, 80, 10)
    py5.no_fill()
    py5.blend_mode(py5.ADD)

def draw():
    # Keep background without clearing to draw the spirograph cumulatively
    # But occasionally dim it slightly so it doesn't blow out to pure white
    if py5.frame_count % 10 == 0:
        py5.blend_mode(py5.BLEND)
        py5.fill(10, 80, 10, 5)
        py5.no_stroke()
        py5.rect(0, 0, py5.width, py5.height)
        py5.blend_mode(py5.ADD)
        py5.no_fill()

    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    num_points = 12
    for i in range(num_points):
        angle_offset = (py5.TWO_PI / num_points) * i
        
        # Complex oscillatory path
        r1 = py5.width * 0.3 * math.sin(t * 0.5 + angle_offset)
        r2 = py5.width * 0.15 * math.cos(t * 1.3 + angle_offset)
        r3 = py5.width * 0.05 * math.sin(t * 2.7)
        
        x = r1 * math.cos(t * 0.2 + angle_offset) + r2 * math.cos(t * 0.7) + r3 * math.cos(t * 3.1)
        y = r1 * math.sin(t * 0.2 + angle_offset) + r2 * math.sin(t * 0.7) + r3 * math.sin(t * 3.1)
        
        hue = (i * (360 / num_points) + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 90, 80, 150)
        py5.stroke_weight(2)
        
        # Draw a shape at the calculated point
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(t * 2 + angle_offset)
        
        # Draw a small geometric motif
        radius = 40 * (1 + math.sin(t + angle_offset))
        py5.ellipse(0, 0, radius, radius * 0.3)
        py5.pop_matrix()

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
