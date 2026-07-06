from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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

# Grid size for fluid
RES = 2
COLS = SIZE[0] // RES
ROWS = SIZE[1] // RES

# Fields
density_r = np.zeros((ROWS, COLS), dtype=np.float32)
density_g = np.zeros((ROWS, COLS), dtype=np.float32)
density_b = np.zeros((ROWS, COLS), dtype=np.float32)

x_coords, y_coords = np.meshgrid(np.arange(COLS), np.arange(ROWS))


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    

def draw():
    global density_r, density_g, density_b
    
    t = py5.frame_count * 0.02
    
    # Emitters
    for i in range(3):
        # 3 moving emitters
        ex = int((math.sin(t * (0.5 + i * 0.1)) * 0.4 + 0.5) * COLS)
        ey = int((math.cos(t * (0.6 + i * 0.15)) * 0.4 + 0.5) * ROWS)
        
        # Inject density
        radius = 15
        mask = (x_coords - ex)**2 + (y_coords - ey)**2 < radius**2
        
        if i == 0:
            density_r[mask] += 25.0
            density_b[mask] += 10.0
        elif i == 1:
            density_g[mask] += 25.0
            density_b[mask] += 20.0
        else:
            density_b[mask] += 25.0
            density_r[mask] += 15.0

    # Calculate curl noise velocity field
    nx = py5.os_noise(x_coords * 0.01, y_coords * 0.01, t * 0.5) * 2 - 1
    ny = py5.os_noise(x_coords * 0.01 + 100, y_coords * 0.01 + 100, t * 0.5) * 2 - 1
    
    # Advect density (semi-Lagrangian backward tracing)
    # Fast advection using nearest neighbor mapping
    back_x = np.clip(x_coords - nx * 4, 0, COLS - 1).astype(np.int32)
    back_y = np.clip(y_coords - ny * 4, 0, ROWS - 1).astype(np.int32)
    
    # Dissipate
    decay = 0.985
    
    density_r = density_r[back_y, back_x] * decay
    density_g = density_g[back_y, back_x] * decay
    density_b = density_b[back_y, back_x] * decay
    
    # Render using np_pixels directly
    py5.load_np_pixels()
    
    # Need to upsample or map if RES > 1, but we can do a block map
    dr_clip = np.clip(density_r, 0, 255).astype(np.uint8)
    dg_clip = np.clip(density_g, 0, 255).astype(np.uint8)
    db_clip = np.clip(density_b, 0, 255).astype(np.uint8)
    
    
    if RES > 1:
        # Nearest neighbor scale up
        dr_clip = np.repeat(np.repeat(dr_clip, RES, axis=0), RES, axis=1)[:SIZE[1], :SIZE[0]]
        dg_clip = np.repeat(np.repeat(dg_clip, RES, axis=0), RES, axis=1)[:SIZE[1], :SIZE[0]]
        db_clip = np.repeat(np.repeat(db_clip, RES, axis=0), RES, axis=1)[:SIZE[1], :SIZE[0]]
        
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = dr_clip
    py5.np_pixels[..., 2] = dg_clip
    py5.np_pixels[..., 3] = db_clip
        
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
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
