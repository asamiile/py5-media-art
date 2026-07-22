from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np
from scipy.signal import convolve2d

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Reaction-diffusion parameters
W, H = 200, 200
A = np.ones((W, H), dtype=np.float32)
B = np.zeros((W, H), dtype=np.float32)

# Feed and kill rates, varying across space
feed = np.linspace(0.010, 0.080, W).reshape((W, 1))
kill = np.linspace(0.045, 0.065, H).reshape((1, H))

# Seed initial areas
for _ in range(20):
    x, y = random.randint(40, W-40), random.randint(40, H-40)
    B[x-5:x+5, y-5:y+5] = 1.0

# Laplacian kernel
kernel = np.array([[0.05, 0.2, 0.05],
                   [0.2, -1.0, 0.2],
                   [0.05, 0.2, 0.05]], dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def update_reaction_diffusion():
    global A, B
    for _ in range(4): # multiple steps per frame
        lapA = convolve2d(A, kernel, mode='same', boundary='wrap')
        lapB = convolve2d(B, kernel, mode='same', boundary='wrap')
        
        reaction = A * B**2
        
        nA = A + (1.0 * lapA - reaction + feed * (1 - A))
        nB = B + (0.5 * lapB + reaction - (feed + kill) * B)
        
        A = np.clip(nA, 0, 1)
        B = np.clip(nB, 0, 1)

def draw():
    global A, B
    py5.background(0)
    
    update_reaction_diffusion()
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    py5.no_stroke()
    
    # Render the grid in isometric projection
    grid_w = SIZE[0] * 0.7
    grid_h = SIZE[1] * 0.7
    cell_w = grid_w / W
    cell_h = grid_h / H
    
    # 2D projection rotation
    # To get isometric-ish view, we rotate around Z, then scale Y to fake tilt
    rot_angle = t * 0.5
    cos_a = math.cos(rot_angle)
    sin_a = math.sin(rot_angle)
    
    # We will draw points to be fast
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    
    for i in range(W):
        for j in range(H):
            val = B[i, j]
            if val > 0.1:
                # Map 0..1 to color
                if val > 0.3:
                    py5.stroke(128, 255, 0, 200) # Lime green
                elif val > 0.2:
                    py5.stroke(255, 255, 0, 150) # Yellow
                else:
                    py5.stroke(128, 0, 255, 100) # Violet
                
                # 3D position
                x = (i - W/2) * cell_w
                y = (j - H/2) * cell_h
                z = val * 300.0
                
                # Rotate around Z (up) axis
                rx = x * cos_a - y * sin_a
                ry = x * sin_a + y * cos_a
                
                # Tilt projection
                screen_x = rx
                screen_y = ry * 0.5 - z
                
                py5.vertex(screen_x, screen_y)
                
    py5.end_shape()

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
