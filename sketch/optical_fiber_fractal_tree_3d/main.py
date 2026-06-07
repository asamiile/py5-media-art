from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)

def draw_branch(len_branch, weight, depth, t):
    if depth == 0:
        return
        
    py5.stroke_weight(weight)
    
    # Calculate color based on depth and time
    hue = (180 + depth * 20 + py5.frame_count * 2) % 360
    py5.stroke(hue, 80, 90, 50)
    
    py5.line(0, 0, 0, 0, -len_branch, 0)
    
    py5.translate(0, -len_branch, 0)
    
    # Gentle wind based on noise
    wind = py5.remap(py5.os_noise(depth * 0.1, t * 0.5), -1, 1, -py5.PI/8, py5.PI/8)
    
    num_branches = 3
    for i in range(num_branches):
        py5.push_matrix()
        angle_z = py5.remap(i, 0, num_branches, -py5.PI/3, py5.PI/3) + wind
        angle_x = py5.remap(py5.os_noise(i, depth, t), -1, 1, -py5.PI/4, py5.PI/4)
        
        py5.rotate_z(angle_z)
        py5.rotate_x(angle_x)
        
        draw_branch(len_branch * 0.7, weight * 0.6, depth - 1, t)
        py5.pop_matrix()

def draw():
    py5.background(220, 90, 5) # Dark blue/black
    
    t = py5.frame_count * 0.02
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height, -500)
    py5.rotate_y(t * 0.5)
    
    draw_branch(450, 15, 6, t)
    
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES*100):.1f}%)")

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
            
        import os
        os._exit(0)

py5.run_sketch()
