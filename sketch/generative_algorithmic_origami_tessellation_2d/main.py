from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Origami tessellation grid
GRID_W = 60
GRID_H = 40
CELL_SIZE = 80
OFFSET_X = -GRID_W * CELL_SIZE / 2
OFFSET_Y = -GRID_H * CELL_SIZE * 0.866 / 2

# Colors
COLOR_A = (245, 220, 230)
COLOR_B = (220, 240, 250)
COLOR_C = (235, 235, 240)


def get_color(x, y, z):
    # Simple color mix based on height
    norm_z = np.clip((z + 150) / 300, 0, 1)
    r = int(COLOR_A[0] * norm_z + COLOR_B[0] * (1 - norm_z))
    g = int(COLOR_A[1] * norm_z + COLOR_B[1] * (1 - norm_z))
    b = int(COLOR_A[2] * norm_z + COLOR_B[2] * (1 - norm_z))
    return py5.color(r, g, b, 230)


def iso_project(x, y, z):
    # Isometric projection
    iso_x = (x - y) * 0.866
    iso_y = (x + y) * 0.5 - z
    return iso_x + py5.width / 2, iso_y + py5.height / 2 + 100


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.noise_seed(random.randint(0, 10000))


def draw():
    py5.background(10, 15, 25)
    
    time_t = py5.frame_count * 0.015
    
    py5.stroke(255, 255, 255, 150)
    py5.stroke_weight(2)

    # Draw hexagonal triangle grid
    py5.begin_shape(py5.TRIANGLES)
    for j in range(GRID_H - 1):
        for i in range(GRID_W - 1):
            x = i * CELL_SIZE + (CELL_SIZE / 2 if j % 2 else 0) + OFFSET_X
            y = j * CELL_SIZE * 0.866 + OFFSET_Y
            
            x_next = (i + 1) * CELL_SIZE + (CELL_SIZE / 2 if j % 2 else 0) + OFFSET_X
            y_next = y
            
            x_bot = i * CELL_SIZE + (CELL_SIZE / 2 if (j+1) % 2 else 0) + OFFSET_X
            y_bot = (j + 1) * CELL_SIZE * 0.866 + OFFSET_Y
            
            x_bot_next = (i + 1) * CELL_SIZE + (CELL_SIZE / 2 if (j+1) % 2 else 0) + OFFSET_X
            y_bot_next = (j + 1) * CELL_SIZE * 0.866 + OFFSET_Y

            # Z displacements
            z1 = (py5.noise(i * 0.1, j * 0.1, time_t) - 0.5) * 300
            z2 = (py5.noise((i + 1) * 0.1, j * 0.1, time_t) - 0.5) * 300
            z3 = (py5.noise(i * 0.1, (j + 1) * 0.1, time_t) - 0.5) * 300
            z4 = (py5.noise((i + 1) * 0.1, (j + 1) * 0.1, time_t) - 0.5) * 300

            ix1, iy1 = iso_project(x, y, z1)
            ix2, iy2 = iso_project(x_next, y_next, z2)
            ix3, iy3 = iso_project(x_bot, y_bot, z3)
            ix4, iy4 = iso_project(x_bot_next, y_bot_next, z4)

            # Triangle 1
            py5.fill(get_color(x, y, (z1 + z2 + z3)/3))
            py5.vertex(ix1, iy1)
            py5.vertex(ix2, iy2)
            py5.vertex(ix3, iy3)
            
            # Triangle 2
            py5.fill(get_color(x, y, (z2 + z3 + z4)/3))
            py5.vertex(ix2, iy2)
            py5.vertex(ix4, iy4)
            py5.vertex(ix3, iy3)
            
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
