from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_SIZE = 60
TILE_W = 40
TILE_H = 20

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(15, 5, 25)
    
    py5.translate(SIZE[0] / 2, SIZE[1] * 0.2)
    
    t = py5.frame_count * 0.01
    
    # Pre-calculate noise for the whole grid to avoid loop overhead
    grid_x, grid_y = np.mgrid[0:GRID_SIZE, 0:GRID_SIZE]
    noise_vals = py5.os_noise(grid_x * 0.05 + t, grid_y * 0.05 + t, t * 0.5)
    
    # Flatten and sort by drawing order (back to front)
    # Isometric sorting: smaller (y+x) draws first
    # Or just iterate in standard y, x order since that is back to front naturally
    
    py5.no_stroke()
    
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            n = noise_vals[x, y]
            
            # Iso mapping
            # (x, y) grid coordinates
            iso_x = (x - y) * (TILE_W / 2)
            iso_y = (x + y) * (TILE_H / 2)
            
            # Building height based on noise
            # Give it some plateau effects using power
            h_norm = max(0.0, (n - 0.2) / 0.8)
            height = h_norm**3 * 800 + 10
            
            # Colors based on height
            r = int(py5.lerp(10, 255, h_norm))
            g = int(py5.lerp(10, 100, h_norm))
            b = int(py5.lerp(60, 0, h_norm))
            
            # Top face
            py5.fill(r + 40, g + 40, b + 40)
            py5.begin_shape()
            py5.vertex(iso_x, iso_y - height)
            py5.vertex(iso_x + TILE_W/2, iso_y + TILE_H/2 - height)
            py5.vertex(iso_x, iso_y + TILE_H - height)
            py5.vertex(iso_x - TILE_W/2, iso_y + TILE_H/2 - height)
            py5.end_shape(py5.CLOSE)
            
            # Left face
            py5.fill(r, g, b)
            py5.begin_shape()
            py5.vertex(iso_x - TILE_W/2, iso_y + TILE_H/2 - height)
            py5.vertex(iso_x, iso_y + TILE_H - height)
            py5.vertex(iso_x, iso_y + TILE_H)
            py5.vertex(iso_x - TILE_W/2, iso_y + TILE_H/2)
            py5.end_shape(py5.CLOSE)
            
            # Right face
            py5.fill(max(0, r - 30), max(0, g - 30), max(0, b - 30))
            py5.begin_shape()
            py5.vertex(iso_x, iso_y + TILE_H - height)
            py5.vertex(iso_x + TILE_W/2, iso_y + TILE_H/2 - height)
            py5.vertex(iso_x + TILE_W/2, iso_y + TILE_H/2)
            py5.vertex(iso_x, iso_y + TILE_H)
            py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
