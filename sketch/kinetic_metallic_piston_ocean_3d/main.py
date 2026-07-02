from pathlib import Path
import shutil
import subprocess
import sys
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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(210, 80, 10) # Dark navy
    py5.directional_light(200, 30, 90, 0, 1, -1)
    py5.directional_light(300, 50, 80, -1, 0, 0)
    py5.ambient_light(220, 40, 20)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 + 300, -800)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(py5.frame_count * 0.005)
    
    grid_size = 40
    box_size = 40
    spacing = 45
    t = py5.frame_count * 0.02
    
    offset = grid_size * spacing / 2
    py5.translate(-offset, -offset, 0)
    
    for x in range(grid_size):
        for y in range(grid_size):
            py5.push_matrix()
            py5.translate(x * spacing, y * spacing, 0)
            
            n_val = py5.os_noise(x * 0.05, y * 0.05, t)
            h = 50 + (((n_val + 1) / 2) ** 3) * 600
            
            hue = py5.remap(n_val, -1, 1, 180, 240)
            py5.fill(hue, 80, 90)
            
            py5.translate(0, 0, h / 2)
            py5.box(box_size, box_size, h)
            py5.pop_matrix()
            
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
