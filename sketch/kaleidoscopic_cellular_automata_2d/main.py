from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global cols, rows, grid, next_grid, hex_size
    hex_size = 8
    # Make a grid big enough to cover a wedge of the screen
    cols = 120
    rows = 120
    grid = np.zeros((cols, rows), dtype=np.float32)
    next_grid = np.zeros((cols, rows), dtype=np.float32)
    
    # Initialize some seeds
    for _ in range(50):
        grid[np.random.randint(0, cols), np.random.randint(0, rows)] = 1.0

def get_neighbors(x, y):
    # Hexagonal neighbors in 2D array (axial coordinates)
    dirs = [
        (1, 0), (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ]
    total = 0.0
    for dx, dy in dirs:
        nx, ny = (x + dx) % cols, (y + dy) % rows
        total += grid[nx, ny]
    return total

def draw():
    # Background fade
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 80, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global grid, next_grid
    
    # Update CA
    for x in range(cols):
        for y in range(rows):
            n = get_neighbors(x, y)
            val = grid[x, y]
            
            # Continuous CA rules
            if val > 0:
                # Decay
                next_grid[x, y] = val - 0.05
                if next_grid[x, y] < 0:
                    next_grid[x, y] = 0
            else:
                # Growth
                if 2.0 <= n <= 3.5:
                    next_grid[x, y] = 1.0
                    
            # Random spontaneous growth
            if py5.random(1) < 0.0001:
                next_grid[x, y] = 1.0

    # Swap grids
    grid = next_grid.copy()
    
    t = py5.frame_count * 0.01
    
    # Draw kaleidoscopic wedges
    num_wedges = 6
    angle_step = py5.TWO_PI / num_wedges
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.rotate(t * 0.5)
    
    w = hex_size * np.sqrt(3)
    h = hex_size * 2
    
    for wedge in range(num_wedges):
        py5.push_matrix()
        py5.rotate(wedge * angle_step)
        
        # Draw the wedge
        py5.no_stroke()
        for x in range(cols):
            for y in range(rows):
                val = grid[x, y]
                if val > 0:
                    px = w * (x + y/2.0)
                    py5.push_matrix()
                    py5.translate(px, pyy := h * (3.0/4.0) * y)
                    # Scale based on value
                    s = val * hex_size * 1.5
                    hue = (200 + x * 2 + y * 2 + t * 50) % 360
                    py5.fill(hue, 90, 100, val * 100)
                    py5.circle(0, 0, s)
                    py5.pop_matrix()
                    
        py5.pop_matrix()
        
        # Draw mirrored wedge
        py5.push_matrix()
        py5.rotate(wedge * angle_step)
        py5.scale(-1, 1) # mirror across y axis
        
        py5.no_stroke()
        for x in range(cols):
            for y in range(rows):
                val = grid[x, y]
                if val > 0:
                    px = w * (x + y/2.0)
                    py5.push_matrix()
                    py5.translate(px, pyy := h * (3.0/4.0) * y)
                    s = val * hex_size * 1.5
                    hue = (200 + x * 2 + y * 2 + t * 50) % 360
                    py5.fill(hue, 90, 100, val * 100)
                    py5.circle(0, 0, s)
                    py5.pop_matrix()
                    
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
