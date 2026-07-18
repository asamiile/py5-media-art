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
    
def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    py5.background(280, 80, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    py5.no_fill()
    py5.stroke_weight(2.5)
    
    steps = 15000 
    loops = 45
    
    r1, r2, r3 = 450, 300, 150
    f1x, f1y = 5, 4
    f2x, f2y = 11, 13
    f3x, f3y = 23, 19
    
    px1 = math.cos(loop_t) * py5.PI
    py1 = math.sin(loop_t) * py5.PI
    
    px2 = math.cos(loop_t * 2) * py5.PI
    py2 = math.sin(loop_t * 2) * py5.PI
    
    px3 = math.cos(loop_t * 3) * py5.PI
    py3 = math.sin(loop_t * 3) * py5.PI

    py5.begin_shape(py5.LINES)
    
    for i in range(steps):
        theta = (i / steps) * py5.TWO_PI * loops
        theta_next = ((i + 1) / steps) * py5.TWO_PI * loops
        
        x1 = r1 * math.sin(f1x * theta + px1) + r2 * math.sin(f2x * theta + px2) + r3 * math.sin(f3x * theta + px3)
        y1 = r1 * math.cos(f1y * theta + py1) + r2 * math.cos(f2y * theta + py2) + r3 * math.cos(f3y * theta + py3)
        
        x2 = r1 * math.sin(f1x * theta_next + px1) + r2 * math.sin(f2x * theta_next + px2) + r3 * math.sin(f3x * theta_next + px3)
        y2 = r1 * math.cos(f1y * theta_next + py1) + r2 * math.cos(f2y * theta_next + py2) + r3 * math.cos(f3y * theta_next + py3)
        
        hue = (i / steps * 360 * 5 + t * 360) % 360
        py5.stroke(hue, 90, 80, 80)
        
        py5.vertex(x1, y1)
        py5.vertex(x2, y2)
        
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
