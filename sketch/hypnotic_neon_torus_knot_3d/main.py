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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_fill()

def draw():
    py5.background(240, 90, 5) # Deep indigo
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    time = (py5.frame_count % TOTAL_FRAMES) / TOTAL_FRAMES
    
    py5.rotate_x(time * py5.TWO_PI)
    py5.rotate_y(time * py5.TWO_PI * 2)
    py5.rotate_z(time * py5.TWO_PI * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    num_strands = 5
    num_points = 300
    
    for strand in range(num_strands):
        py5.begin_shape(py5.LINE_STRIP)
        
        hue_val = (strand * 72 + time * 360) % 360
        py5.stroke(hue_val, 90, 100, 200)
        py5.stroke_weight(20)
        
        for i in range(num_points + 1):
            theta = (i / num_points) * py5.TWO_PI
            
            # Torus knot parameters (p=3, q=4)
            p = 3
            q = 4
            
            r1 = 500
            r2 = 250
            
            offset = strand * py5.TWO_PI / num_strands
            
            x = (r1 + r2 * math.cos(q * theta + offset)) * math.cos(p * theta)
            y = (r1 + r2 * math.cos(q * theta + offset)) * math.sin(p * theta)
            z = r2 * math.sin(q * theta + offset)
            
            py5.vertex(x, y, z)
            
        py5.end_shape()

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
