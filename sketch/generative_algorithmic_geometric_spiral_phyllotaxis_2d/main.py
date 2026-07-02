from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math

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

C_PARAM = 25.0 # Scaling factor

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 15, 20)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    time_offset = py5.frame_count * 2.0
    
    # Draw from outside in to handle overlap correctly if needed, or inside out
    for n in range(3000, 0, -1):
        # Calculate offset n
        n_val = n + time_offset
        
        # Phyllotaxis formula
        theta = n_val * 137.508 * (math.pi / 180.0)
        r = C_PARAM * math.sqrt(n_val)
        
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        
        # Don't draw if too far outside
        if x < -SIZE[0]/2 - 100 or x > SIZE[0]/2 + 100 or y < -SIZE[1]/2 - 100 or y > SIZE[1]/2 + 100:
            continue
            
        hue = (n_val * 0.1 + py5.frame_count * 0.5) % 360
        bri = py5.remap(math.sqrt(n_val), 0, 80, 100, 20)
        size = py5.remap(math.sqrt(n_val), 0, 80, 5, 40)
        
        py5.fill(hue, 80, bri)
        
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(theta + py5.frame_count * 0.05)
        
        # Draw a triangle
        py5.begin_shape()
        py5.vertex(0, -size)
        py5.vertex(-size*0.866, size*0.5)
        py5.vertex(size*0.866, size*0.5)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
