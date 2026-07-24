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

# Grid size (use slightly lower resolution for speed, then upscale)
SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

STEPS_PER_FRAME = 20

# Gray-Scott Parameters
Da = 1.0
Db = 0.5
dt = 1.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global A, B, x, y, colormap
    
    # Initialize concentrations
    A = np.ones((H, W), dtype=np.float32)
    B = np.zeros((H, W), dtype=np.float32)
    
    # Seed with random squares of B
    for _ in range(50):
        rx = np.random.randint(10, W-10)
        ry = np.random.randint(10, H-10)
        B[ry-5:ry+5, rx-5:rx+5] = 1.0
        
    y, x = np.ogrid[0:H, 0:W]
    
    # Pre-generate a colormap for rendering (map values 0-255 to colors)
    # Deep blue/black to Cyan to White to Magenta
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        # Color mapping logic
        if v < 0.3:
            # 0.0 - 0.3: Black to Deep Blue
            p = v / 0.3
            colormap[i, 1:] = [0, 0, int(p * 150)]
        elif v < 0.6:
            # 0.3 - 0.6: Deep Blue to Cyan
            p = (v - 0.3) / 0.3
            colormap[i, 1:] = [0, int(p * 255), 150 + int(p * 105)]
        elif v < 0.8:
            # 0.6 - 0.8: Cyan to White
            p = (v - 0.6) / 0.2
            colormap[i, 1:] = [int(p * 255), 255, 255]
        else:
            # 0.8 - 1.0: White to Magenta
            p = (v - 0.8) / 0.2
            colormap[i, 1:] = [255, 255 - int(p * 255), 255]

def draw():
    global A, B
    
    # Dynamic Feed (F) and Kill (K) rates
    # Animate them to cause morphological shifts
    t = py5.frame_count * 0.02
    
    # F varies roughly [0.01, 0.07]
    F = 0.04 + 0.025 * np.sin(x * 0.005 + t) * np.cos(y * 0.003 - t * 0.5)
    
    # K varies roughly [0.045, 0.065]
    K = 0.055 + 0.008 * np.cos(x * 0.004 - t * 0.7) * np.sin(y * 0.006 + t)
    
    for _ in range(STEPS_PER_FRAME):
        # Laplacian calculation using np.roll (faster than scipy.ndimage.convolve for simple 3x3)
        # Using a 9-point stencil for better stability
        # [0.05, 0.2, 0.05]
        # [0.2,  -1,  0.2 ]
        # [0.05, 0.2, 0.05]
        
        # Cross neighbors
        cross_A = np.roll(A, 1, 0) + np.roll(A, -1, 0) + np.roll(A, 1, 1) + np.roll(A, -1, 1)
        cross_B = np.roll(B, 1, 0) + np.roll(B, -1, 0) + np.roll(B, 1, 1) + np.roll(B, -1, 1)
        
        # Diagonal neighbors
        diag_A = np.roll(np.roll(A, 1, 0), 1, 1) + np.roll(np.roll(A, 1, 0), -1, 1) + \
                 np.roll(np.roll(A, -1, 0), 1, 1) + np.roll(np.roll(A, -1, 0), -1, 1)
                 
        diag_B = np.roll(np.roll(B, 1, 0), 1, 1) + np.roll(np.roll(B, 1, 0), -1, 1) + \
                 np.roll(np.roll(B, -1, 0), 1, 1) + np.roll(np.roll(B, -1, 0), -1, 1)
                 
        lapA = cross_A * 0.2 + diag_A * 0.05 - A
        lapB = cross_B * 0.2 + diag_B * 0.05 - B
        
        # Reaction
        reaction = A * B * B
        
        # Update
        A = np.clip(A + (Da * lapA - reaction + F * (1.0 - A)) * dt, 0.0, 1.0)
        B = np.clip(B + (Db * lapB + reaction - (K + F) * B) * dt, 0.0, 1.0)
        
    py5.load_np_pixels()
    
    # Normalize B for visualization (B is usually small, so we scale it up for the colormap)
    b_vis = np.clip(B * 3.0, 0.0, 1.0)
    color_indices = (b_vis * 255).astype(np.uint8)
    
    img_data = colormap[color_indices]
    
    # Scale up if necessary
    if SCALE > 1:
        img_data = np.repeat(np.repeat(img_data, SCALE, axis=0), SCALE, axis=1)
        
    py5.np_pixels[:] = img_data
    py5.update_np_pixels()

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
