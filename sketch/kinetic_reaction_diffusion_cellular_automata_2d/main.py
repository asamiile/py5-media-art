from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5
from scipy.ndimage import convolve

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

# Reaction diffusion parameters
DA = 1.0
DB = 0.5
feed = 0.055
kill = 0.062
dt = 1.0

# Simulation resolution
sim_scale = 4
sim_w = SIZE[0] // sim_scale
sim_h = SIZE[1] // sim_scale

A = np.ones((sim_h, sim_w), dtype=np.float32)
B = np.zeros((sim_h, sim_w), dtype=np.float32)

laplacian = np.array([
    [0.05, 0.2, 0.05],
    [0.2, -1.0, 0.2],
    [0.05, 0.2, 0.05]
], dtype=np.float32)

rgba_data = np.zeros((sim_h, sim_w, 4), dtype=np.uint8)
img = None

def setup():
    global A, B, img
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed B
    for _ in range(20):
        rx = np.random.randint(0, sim_w - 20)
        ry = np.random.randint(0, sim_h - 20)
        B[ry:ry+20, rx:rx+20] = 1.0
        
    img = py5.create_image(sim_w, sim_h, py5.ARGB)

def draw():
    global A, B, img, feed, kill, rgba_data
    
    # Morph parameters slightly over time to change patterns
    t = py5.frame_count * 0.005
    f = feed + np.sin(t * 1.5) * 0.01
    k = kill + np.cos(t * 1.2) * 0.005
    
    # Run a few simulation steps per frame for speed
    for _ in range(8):
        lapA = convolve(A, laplacian, mode='reflect')
        lapB = convolve(B, laplacian, mode='reflect')
        
        ABB = A * B * B
        A = A + (DA * lapA - ABB + f * (1 - A)) * dt
        B = B + (DB * lapB + ABB - (f + k) * B) * dt

    # Colorize
    # B ranges roughly 0 to 0.5. Scale to 0-255
    B_norm = np.clip(B * 2.5, 0, 1)
    
    # Bioluminescent colors
    # Cyan (0, 255, 255) to Deep Pink (255, 20, 147) mapped by B concentration
    rgba_data[..., 0] = (B_norm * 255).astype(np.uint8) # R
    rgba_data[..., 1] = ((1 - B_norm) * B_norm * 4 * 255).astype(np.uint8) # G
    rgba_data[..., 2] = (B_norm * 147 + (1 - B_norm) * 255).astype(np.uint8) # B
    rgba_data[..., 3] = 255 # A
    
    img.set_np_pixels(rgba_data)
    
    # Draw scaled
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

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
