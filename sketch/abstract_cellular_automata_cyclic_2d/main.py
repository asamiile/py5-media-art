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

sim_w = 480
sim_h = 270

num_states = 14
threshold = 1

grid = np.random.randint(0, num_states, (sim_h, sim_w), dtype=np.int32)
img = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global img
    img = py5.create_image(sim_w, sim_h, py5.RGB)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    global grid, img
    
    for _ in range(2):
        target = (grid + 1) % num_states
        
        neighbors = (
            (np.roll(grid, 1, axis=0) == target).astype(int) +
            (np.roll(grid, -1, axis=0) == target).astype(int) +
            (np.roll(grid, 1, axis=1) == target).astype(int) +
            (np.roll(grid, -1, axis=1) == target).astype(int) +
            (np.roll(np.roll(grid, 1, axis=0), 1, axis=1) == target).astype(int) +
            (np.roll(np.roll(grid, 1, axis=0), -1, axis=1) == target).astype(int) +
            (np.roll(np.roll(grid, -1, axis=0), 1, axis=1) == target).astype(int) +
            (np.roll(np.roll(grid, -1, axis=0), -1, axis=1) == target).astype(int)
        )
        
        mask = neighbors >= threshold
        grid = np.where(mask, target, grid)

    img.load_np_pixels()
    
    t = py5.frame_count * 0.02
    
    hue_offset = t * 100
    
    hues = (grid * (360 / num_states) + hue_offset) % 360
    
    r_val = (np.sin(hues * np.pi / 180) * 127 + 128).astype(np.uint8)
    g_val = (np.sin((hues + 120) * np.pi / 180) * 127 + 128).astype(np.uint8)
    b_val = (np.sin((hues + 240) * np.pi / 180) * 127 + 128).astype(np.uint8)
    
    img.np_pixels[:, :, 0] = r_val
    img.np_pixels[:, :, 1] = g_val
    img.np_pixels[:, :, 2] = b_val
    img.np_pixels[:, :, 3] = 255
    
    img.update_np_pixels()
    
    py5.background(0)
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
