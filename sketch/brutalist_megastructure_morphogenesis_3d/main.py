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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(15, 18, 22)
    
    # Brutalist lighting: strong harsh main light, cool fill light
    py5.ambient_light(40, 45, 55)
    py5.directional_light(255, 230, 200, 0.8, 0.5, -0.5)
    py5.directional_light(80, 120, 200, -0.8, -0.5, 0.5)
    
    py5.translate(py5.width / 2, py5.height / 2, -1200)
    
    t = py5.frame_count * 0.008
    
    # Slow, majestic rotation
    py5.rotate_x(-py5.PI / 8)
    py5.rotate_y(py5.PI / 4 + t * 0.15)
    
    grid_size = 20
    box_size = 100
    offset = box_size * 1.05
    
    # Center the grid
    py5.translate(-grid_size * offset / 2, -grid_size * offset / 2, -grid_size * offset / 2)
    
    py5.no_stroke()
    
    for x in range(grid_size):
        for y in range(grid_size):
            for z in range(grid_size):
                # 3D noise field moving in time
                n_val = py5.os_noise(x * 0.1, y * 0.1, z * 0.1 + t * 0.5)
                
                if n_val > 0.0: # Threshold
                    # Architectural scaling
                    scale_x = py5.remap(n_val, 0.0, 1.0, 0, box_size * 1.5)
                    scale_y = py5.remap(py5.os_noise(x * 0.1, y * 0.1 + 10, z * 0.1), -1, 1, box_size * 0.2, box_size * 4.0)
                    scale_z = py5.remap(n_val, 0.0, 1.0, 0, box_size * 1.5)
                    
                    py5.push_matrix()
                    py5.translate(x * offset, y * offset, z * offset)
                    
                    # Concrete color with slight depth variations
                    c_base = py5.remap(y, 0, grid_size, 80, 220)
                    r = py5.constrain(c_base * n_val, 0, 255)
                    g = py5.constrain(c_base * n_val * 0.95, 0, 255)
                    b = py5.constrain(c_base * n_val * 0.9, 0, 255)
                    
                    py5.fill(r, g, b)
                    py5.box(scale_x, scale_y, scale_z)
                    py5.pop_matrix()
                    
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
