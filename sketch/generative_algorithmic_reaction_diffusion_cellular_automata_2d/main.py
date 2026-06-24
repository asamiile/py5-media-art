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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global gridA, gridB, nextA, nextB, DA, DB, feed, kill, w, h
    # Scale down grid for performance of reaction diffusion
    w = py5.width // 4
    h = py5.height // 4
    
    gridA = np.ones((w, h))
    gridB = np.zeros((w, h))
    nextA = np.zeros((w, h))
    nextB = np.zeros((w, h))
    
    DA = 1.0
    DB = 0.5
    feed = 0.055
    kill = 0.062
    
    # Seed
    for i in range(100):
        sx = py5.random_int(20, w - 20)
        sy = py5.random_int(20, h - 20)
        gridB[sx-5:sx+5, sy-5:sy+5] = 1.0

def laplace(grid):
    # Quick 3x3 laplacian using numpy slicing
    lap = np.zeros_like(grid)
    lap[1:-1, 1:-1] = (
        grid[1:-1, 1:-1] * -1.0 +
        grid[0:-2, 1:-1] * 0.2 +
        grid[2:, 1:-1] * 0.2 +
        grid[1:-1, 0:-2] * 0.2 +
        grid[1:-1, 2:] * 0.2 +
        grid[0:-2, 0:-2] * 0.05 +
        grid[2:, 0:-2] * 0.05 +
        grid[0:-2, 2:] * 0.05 +
        grid[2:, 2:] * 0.05
    )
    return lap

def draw():
    global gridA, gridB, nextA, nextB
    
    # Evolve a few steps per frame
    for _ in range(5):
        lapA = laplace(gridA)
        lapB = laplace(gridB)
        
        abb = gridA * gridB * gridB
        
        # Vary feed/kill across space dynamically
        fx = np.linspace(0.01, 0.08, w)[:, None]
        ky = np.linspace(0.045, 0.07, h)[None, :]
        f = feed + 0.02 * np.sin(py5.frame_count * 0.01 + fx)
        k = kill + 0.01 * np.cos(py5.frame_count * 0.01 + ky)
        
        nextA = gridA + (DA * lapA - abb + f * (1 - gridA))
        nextB = gridB + (DB * lapB + abb - (k + f) * gridB)
        
        nextA = np.clip(nextA, 0, 1)
        nextB = np.clip(nextB, 0, 1)
        
        gridA, nextA = nextA, gridA
        gridB, nextB = nextB, gridB
        
    py5.background(0)
    py5.color_mode(py5.RGB, 255)
    
    # Map the low-res grid to the full screen pixels
    c = gridA - gridB
    c_norm = np.clip(c, 0, 1)
    
    # Very crude mapping for speed: Draw 4x4 rects
    py5.no_stroke()
    for x in range(0, w, 2): # Skip some for speed if needed, or draw 4x4
        for y in range(0, h, 2):
            diff = gridA[x, y] - gridB[x, y]
            if diff < 0.6: # threshold to only draw the pattern
                val = int((1 - diff) * 255)
                # Psychedelic colors based on frame count
                r = int(val * (0.5 + 0.5 * np.sin(py5.frame_count * 0.05)))
                g = int(val * (0.5 + 0.5 * np.cos(py5.frame_count * 0.03)))
                b = int(val * (0.5 + 0.5 * np.sin(py5.frame_count * 0.02 + 2)))
                py5.fill(r, g, b)
                py5.rect(x * 4, y * 4, 8, 8)

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
            
        import os
        os._exit(0)

py5.run_sketch()
