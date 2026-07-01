from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Lenia / SmoothLife Parameters
# We simulate at 1920x1080 and upscale for rendering
W, H = SIZE[0] // 2, SIZE[1] // 2

# Core parameters (Orbium species roughly)
R = 15.0      # Kernel radius
T = 10.0      # Time step scaling
m = 0.15      # Growth center
s = 0.015     # Growth width

# Kernel generation
cx, cy = W // 2, H // 2
x = np.arange(W) - cx
y = np.arange(H) - cy
XX, YY = np.meshgrid(x, y)
D = np.sqrt(XX**2 + YY**2) / R

# Bell-shaped ring kernel
K = np.exp(4.0 - 1.0 / (D * (1.0 - D) + 1e-6))
K[D >= 1.0] = 0
K[D <= 0.0] = 0
K /= np.sum(K)

# FFT of the kernel (shifted to center for convolution)
K_fft = np.fft.fft2(np.fft.ifftshift(K))

# State
A = np.zeros((H, W), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global A
    # Seed with noise in the center
    seed_r = 100
    mask = (XX**2 + YY**2) <= seed_r**2
    A[mask] = np.random.random(np.sum(mask)).astype(np.float32)
    
    # Pre-simulate to let organisms form
    print("[Setup] Pre-simulating 200 steps to form structures...")
    for _ in range(200):
        step()

def step():
    global A
    # Convolution via FFT
    A_fft = np.fft.fft2(A)
    U = np.real(np.fft.ifft2(A_fft * K_fft))
    
    # Growth function (Gaussian)
    G = np.exp(-((U - m) ** 2) / (2 * s ** 2)) * 2.0 - 1.0
    
    # Euler integration
    A_new = A + (1.0 / T) * G
    A = np.clip(A_new, 0, 1)

def draw():
    global A
    
    # Advance simulation
    # We do a few steps per frame to make it kinetic
    for _ in range(3):
        step()
        
    # Render
    # Map A (0.0 to 1.0) to a bioluminescent colormap
    # Background: dark teal, Organisms: bright green to white
    
    # Nonlinear mapping to boost visibility of faint trails
    A_vis = A ** 0.8
    
    R_channel = (A_vis * A_vis * 255).astype(np.uint8)
    G_channel = (A_vis * 255).astype(np.uint8)
    B_channel = ((A_vis * 0.5 + 0.1) * 255).astype(np.uint8)
    Alpha = np.full((H, W), 255, dtype=np.uint8)
    
    pixels = np.dstack((Alpha, R_channel, G_channel, B_channel))
    
    img = py5.create_image_from_numpy(pixels, 'ARGB')
    
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
