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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 15, 20)
    
def draw():
    py5.no_stroke()
    py5.fill(10, 15, 20, 5) # Very slow fade for long tails
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count * 0.08
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    for _ in range(5):  # Draw multiple interwoven lines
        py5.begin_shape()
        for sub_t in range(0, 150):
            actual_t = t + sub_t * 0.005 + _ * 10.0
            
            a1 = 600 + math.sin(actual_t * 0.05) * 300
            a2 = 400 + math.cos(actual_t * 0.07) * 200
            a3 = 600 + math.cos(actual_t * 0.06) * 300
            a4 = 400 + math.sin(actual_t * 0.08) * 200
            
            f1 = 2.01 + math.sin(actual_t * 0.02) * 0.02
            f2 = 3.0
            f3 = 3.01
            f4 = 2.0 + math.cos(actual_t * 0.02) * 0.02
            
            p1 = actual_t * 0.01
            p2 = actual_t * 0.02
            p3 = py5.PI / 2
            p4 = 0
            
            x = a1 * math.sin(f1 * actual_t + p1) + a2 * math.sin(f2 * actual_t + p2)
            y = a3 * math.sin(f3 * actual_t + p3) + a4 * math.sin(f4 * actual_t + p4)
            
            hue = (200 + x * 0.04 + y * 0.04 + actual_t * 10 + _ * 20) % 360
            py5.stroke(hue, 90, 100, 80)
            py5.vertex(x, y)
            
        py5.end_shape()

    py5.color_mode(py5.RGB, 255)

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
