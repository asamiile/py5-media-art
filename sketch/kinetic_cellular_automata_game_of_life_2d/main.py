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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SCL = 20
COLS = SIZE[0] // SCL
ROWS = SIZE[1] // SCL

state = np.random.choice([0, 1], size=(COLS, ROWS), p=[0.85, 0.15])
smooth_state = np.zeros((COLS, ROWS))

def step_gol(grid):
    # Pad grid with zeros to handle edges easily, or wrap around
    padded = np.pad(grid, 1, mode='wrap')
    # Sum neighbors
    N = (padded[0:-2, 0:-2] + padded[0:-2, 1:-1] + padded[0:-2, 2:] +
         padded[1:-1, 0:-2] +                      padded[1:-1, 2:] +
         padded[2:,   0:-2] + padded[2:,   1:-1] + padded[2:,   2:])
    
    # Apply rules
    birth = (N == 3) & (grid == 0)
    survive = ((N == 2) | (N == 3)) & (grid == 1)
    
    new_grid = np.zeros_like(grid)
    new_grid[birth | survive] = 1
    return new_grid

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global state, smooth_state
    
    # Fade background instead of clearing
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 30, 60)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Step the Game of Life every 6 frames (10 updates per second)
    if py5.frame_count % 6 == 0:
        state = step_gol(state)
        
    # Smoothly interpolate visual state
    smooth_state += (state - smooth_state) * 0.2
    
    py5.blend_mode(py5.ADD)
    
    # Draw connections and nodes
    py5.stroke_weight(2)
    
    # We iterate and draw
    # For performance in py5, we can use begin_shape(LINES) or just loop
    # We have 192 * 108 = 20,736 cells.
    # To optimize, we only process cells where smooth_state > 0.05
    active_indices = np.argwhere(smooth_state > 0.05)
    
    for x, y in active_indices:
        val = smooth_state[x, y]
        px = x * SCL + SCL / 2
        py = y * SCL + SCL / 2
        
        # Color based on position and time
        time_offset = py5.frame_count * 0.01
        hue_shift = py5.remap(py5.os_noise(x * 0.05, y * 0.05, time_offset), -1, 1, 0, 1)
        
        r = py5.lerp(50, 255, hue_shift) * val
        g = py5.lerp(255, 50, hue_shift) * val
        b = py5.lerp(200, 255, val) * val
        
        py5.fill(r, g, b, 255 * val)
        py5.no_stroke()
        py5.circle(px, py, SCL * 0.8 * val)
        
        # Draw connections to right and bottom neighbors if they are also somewhat active
        py5.stroke(r, g, b, 150 * val)
        if x < COLS - 1 and smooth_state[x+1, y] > 0.05:
            val_right = smooth_state[x+1, y]
            py5.line(px, py, px + SCL, py)
            
        if y < ROWS - 1 and smooth_state[x, y+1] > 0.05:
            val_bottom = smooth_state[x, y+1]
            py5.line(px, py, px, py + SCL)

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
