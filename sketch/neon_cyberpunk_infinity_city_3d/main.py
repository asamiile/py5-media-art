import random
import numpy as np
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

np.random.seed()

# Grid settings
COLS = 40
ROWS = 40
BLOCK_SIZE = 80
STREET_WIDTH = 20
TOTAL_SIZE = BLOCK_SIZE + STREET_WIDTH
WIDTH = COLS * TOTAL_SIZE
DEPTH = ROWS * TOTAL_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(5, 5, 10)
    
    t = py5.frame_count * 0.02
    
    # Camera setup (flying over the city)
    cam_x = WIDTH / 2.0
    cam_y = -800 + 200 * np.sin(t * 0.5)
    cam_z = DEPTH / 2.0 + (py5.frame_count * 20.0) % TOTAL_SIZE  # moving forward effect
    
    look_x = WIDTH / 2.0 + 500 * np.sin(t * 0.3)
    look_y = 0
    look_z = cam_z - 1500
    
    py5.camera(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 1, 0)
    
    # Lighting
    py5.ambient_light(20, 20, 30)
    py5.directional_light(200, 100, 100, 0.5, 1, -1)
    py5.directional_light(250, 50, 100, -0.5, 0.5, -0.5)
    
    # Offset for endless scrolling noise
    y_offset = py5.frame_count * 0.05
    
    py5.blend_mode(py5.ADD)
    
    for r in range(ROWS):
        for c in range(COLS):
            # Calculate procedural height
            nx = c * 0.1
            ny = (r - py5.frame_count * 0.2) * 0.1
            
            # Use os_noise to generate heights
            noise_val = py5.os_noise(nx, ny, t * 0.1)
            
            # Central trench (river/highway)
            dist_from_center = abs(c - COLS / 2.0)
            trench_factor = min(1.0, dist_from_center / 5.0)
            
            # Compute final building height
            h = max(20.0, (noise_val + 1.0) * 400.0 * trench_factor)
            
            # Rare supertall skyscrapers
            if (hash((c, r + int(y_offset))) % 100) < 2:
                h *= 3.0
            
            x = c * TOTAL_SIZE
            z = cam_z - r * TOTAL_SIZE
            y = -h / 2.0  # Box is centered at Y, draw it up from ground (y=0)
            
            hue = (200 + h * 0.2 + t * 20) % 360
            if h > 800:
                hue = (hue + 180) % 360  # Contrast color for tall buildings
            
            py5.push_matrix()
            py5.translate(x, y, z)
            
            # Core building
            py5.fill(hue, 80, 50, 80)
            py5.stroke(hue, 100, 100, 90)
            py5.stroke_weight(2)
            py5.box(BLOCK_SIZE, h, BLOCK_SIZE)
            
            py5.pop_matrix()

    # Draw neon floor grid
    py5.stroke(300, 80, 100, 40)
    py5.stroke_weight(1)
    for r in range(ROWS + 1):
        z = cam_z - r * TOTAL_SIZE
        py5.line(0, 0, z, WIDTH, 0, z)
    for c in range(COLS + 1):
        x = c * TOTAL_SIZE
        py5.line(x, 0, cam_z, x, 0, cam_z - DEPTH)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
