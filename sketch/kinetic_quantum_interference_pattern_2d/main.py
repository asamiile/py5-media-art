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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Render at a lower resolution for performance (e.g. 1/4th scale)
# 3840x2160 -> 960x540
SCALE = 4
RENDER_W = SIZE[0] // SCALE
RENDER_H = SIZE[1] // SCALE

pg = None

# Pre-calculate meshgrid
x = np.arange(RENDER_W, dtype=np.float32)
y = np.arange(RENDER_H, dtype=np.float32)
X, Y = np.meshgrid(x, y)

def setup():
    global pg
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    pg = py5.create_graphics(RENDER_W, RENDER_H)

def draw():
    t = py5.frame_count * 0.05
    
    # Moving sources
    # Source 1
    cx1 = RENDER_W/2 + np.cos(t * 0.7) * 200
    cy1 = RENDER_H/2 + np.sin(t * 0.5) * 150
    # Source 2
    cx2 = RENDER_W/2 + np.cos(t * 0.4 + 2.0) * 300
    cy2 = RENDER_H/2 + np.sin(t * 0.8 + 1.0) * 100
    # Source 3
    cx3 = RENDER_W/2 + np.cos(t * 0.9 - 1.0) * 100
    cy3 = RENDER_H/2 + np.sin(t * 0.3 - 2.0) * 200
    
    freq = 0.2
    
    d1 = np.sqrt((X - cx1)**2 + (Y - cy1)**2)
    d2 = np.sqrt((X - cx2)**2 + (Y - cy2)**2)
    d3 = np.sqrt((X - cx3)**2 + (Y - cy3)**2)
    
    w1 = np.sin(d1 * freq - t * 2.0)
    w2 = np.sin(d2 * freq - t * 2.0)
    w3 = np.sin(d3 * freq - t * 2.0)
    
    # Interference sum
    total = w1 + w2 + w3
    
    # Normalize to roughly -1 to 1, then apply non-linear mapping for sharp fringes
    val = np.sin(total * 2.0) # creates more Moiré
    
    # Map to colors
    # Base black and white
    bw = ((val + 1.0) * 127.5).astype(np.int32)
    
    # Iridescent cyan/magenta on peaks
    r = np.clip(bw + (np.sin(total * 3.0) * 100), 0, 255).astype(np.int32)
    g = np.clip(bw + (np.cos(total * 2.0) * 100), 0, 255).astype(np.int32)
    b = np.clip(bw + (np.sin(total * 1.5) * 100 + 50), 0, 255).astype(np.int32)
    pg.begin_draw()
    pg.load_np_pixels()
    
    # Assign to channels directly. In py5 ARGB: A=0, R=1, G=2, B=3
    pg.np_pixels[:, :, 0] = 255
    pg.np_pixels[:, :, 1] = r
    pg.np_pixels[:, :, 2] = g
    pg.np_pixels[:, :, 3] = b
    
    pg.update_np_pixels()
    pg.end_draw()
    
    # Draw scaled up image
    # Use NO_SMOOTH for crisp pixels, or smooth for softer look
    py5.image(pg, 0, 0, SIZE[0], SIZE[1])

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
