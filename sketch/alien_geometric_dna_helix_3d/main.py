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

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    # Global rotation
    progress = (py5.frame_count % TOTAL_FRAMES) / TOTAL_FRAMES
    angle = progress * py5.TWO_PI
    
    py5.rotate_x(angle)
    py5.rotate_y(angle * 0.5)
    
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    num_pairs = 150
    radius = 300
    height_step = 20
    
    total_height = num_pairs * height_step
    py5.translate(0, -total_height / 2, 0)
    
    # Draw helix
    for i in range(num_pairs):
        y = i * height_step
        # 1D noise for organic undulation
        n = py5.noise(i * 0.05, py5.frame_count * 0.02) * 100
        
        # Spiral angle
        theta = i * 0.2 + angle * 2
        
        x1 = math.cos(theta) * (radius + n)
        z1 = math.sin(theta) * (radius + n)
        
        x2 = math.cos(theta + py5.PI) * (radius + n)
        z2 = math.sin(theta + py5.PI) * (radius + n)
        
        # Depth based fading
        alpha = py5.remap(py5.sin(theta), -1, 1, 100, 255)
        
        # Draw base pair connection
        py5.stroke(250, 80, 100, alpha * 0.5)
        py5.stroke_weight(3)
        py5.line(x1, y, z1, x2, y, z2)
        
        # Draw strands
        py5.no_stroke()
        py5.push_matrix()
        py5.translate(x1, y, z1)
        py5.fill(180, 90, 100, alpha) # Teal
        py5.sphere(15)
        py5.pop_matrix()
        
        py5.push_matrix()
        py5.translate(x2, y, z2)
        py5.fill(320, 90, 100, alpha) # Magenta
        py5.sphere(15)
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

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
