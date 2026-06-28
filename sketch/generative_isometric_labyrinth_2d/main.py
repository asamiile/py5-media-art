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

# Isometric drawing helpers
def iso_to_2d(x, y, z):
    # Standard isometric projection
    # 30 degree angle
    alpha = math.pi / 6
    screen_x = (x - y) * math.cos(alpha)
    screen_y = (x + y) * math.sin(alpha) - z
    return screen_x, screen_y

def draw_iso_cube(x, y, z, size, hue, sat, bright):
    # Top face
    py5.fill(hue, sat, bright)
    py5.begin_shape()
    px, py_s = iso_to_2d(x, y, z + size)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y, z + size)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y + size, z + size)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x, y + size, z + size)
    py5.vertex(px, py_s)
    py5.end_shape(py5.CLOSE)
    
    # Left face (darker)
    py5.fill(hue, sat, bright * 0.7)
    py5.begin_shape()
    px, py_s = iso_to_2d(x, y, z)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y, z)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y, z + size)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x, y, z + size)
    py5.vertex(px, py_s)
    py5.end_shape(py5.CLOSE)
    
    # Right face (darkest)
    py5.fill(hue, sat, bright * 0.4)
    py5.begin_shape()
    px, py_s = iso_to_2d(x + size, y, z)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y + size, z)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y + size, z + size)
    py5.vertex(px, py_s)
    px, py_s = iso_to_2d(x + size, y, z + size)
    py5.vertex(px, py_s)
    py5.end_shape(py5.CLOSE)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()

def draw():
    py5.background(10, 80, 15)
    
    t = py5.frame_count * 0.02
    grid = 35
    cell_size = 50
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2 + 200)
    
    # Draw from back to front to avoid depth sorting issues in 2D
    # For isometric, back to front means highest (x+y) first, but wait, (x+y) is depth!
    # Back is smaller x, smaller y
    for x in range(grid):
        for y in range(grid):
            # Evaluate noise to determine if a block exists and its height
            n = py5.os_noise(x * 0.1, y * 0.1, t * 0.5)
            
            # Create a maze-like structure by thresholding noise
            if n > 0.4:
                height_mult = py5.remap(n, 0.4, 1.0, 1, 5)
                z_height = height_mult * cell_size
                
                # Dynamic coloring
                hue = (n * 360 + py5.frame_count * 0.5) % 360
                
                draw_iso_cube(
                    (x - grid/2) * cell_size,
                    (y - grid/2) * cell_size,
                    0,
                    cell_size,
                    hue, 80, 90
                )
    
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
