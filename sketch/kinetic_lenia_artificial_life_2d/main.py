from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.fft import fft2, ifft2

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

# Lenia (Continuous Cellular Automata) Parameters
# We use a 1/2 scale grid for FFT performance, then upscale for rendering
SCALE = 2
SIZE = OUTPUT_SIZE
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

# Orbium-like parameters
R = 25          # Kernel radius
T = 10.0        # Time step denominator (dt = 1/T)
m = 0.15        # Growth center
s = 0.015       # Growth width

def bell(x, m, s):
    return np.exp(-((x - m) / s)**2 / 2)

def generate_kernel(W, H, R):
    # Create coordinate grid centered at (0,0), wrapping around for FFT
    y, x = np.ogrid[-H//2:H//2, -W//2:W//2]
    
    # Distance from center
    r = np.sqrt(x*x + y*y) / R
    
    # Core function (smooth ring)
    # A standard Lenia core: exp( 4 - 1 / (r * (1-r)) ) for r in (0,1)
    K = np.zeros((H, W), dtype=np.float32)
    mask = (r > 0) & (r < 1)
    r_mask = r[mask]
    K[mask] = np.exp(4.0 - 1.0 / (r_mask * (1.0 - r_mask)))
    
    # Normalize so sum is 1
    K /= np.sum(K)
    
    # Shift center to (0,0) for FFT convolution theorem
    K_shifted = np.fft.ifftshift(K)
    return K_shifted

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global A, K_fft, colormap
    
    # Initialize random primordial soup
    # We populate some random blocks of noise rather than full random, to allow structures to form
    A = np.zeros((H, W), dtype=np.float32)
    for _ in range(300):
        size = np.random.randint(10, 40)
        cx = np.random.randint(0, W - size)
        cy = np.random.randint(0, H - size)
        A[cy:cy+size, cx:cx+size] = np.random.uniform(0, 1, (size, size))
    
    # Precompute FFT of Kernel
    K = generate_kernel(W, H, R)
    K_fft = fft2(K)
    
    # Pre-generate a bioluminescent colormap
    # State A goes from 0 to 1
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255
        # Black -> Deep Teal -> Cyan -> White/Green
        if v < 0.2:
            colormap[i, 1:] = [0, int(v/0.2 * 50), int(v/0.2 * 100)]
        elif v < 0.6:
            p = (v - 0.2) / 0.4
            colormap[i, 1:] = [0, 50 + int(p * 150), 100 + int(p * 155)]
        else:
            p = (v - 0.6) / 0.4
            colormap[i, 1:] = [int(p * 255), 200 + int(p * 55), 255]

def step_physics():
    global A
    
    # 1. FFT Convolution
    A_fft = fft2(A)
    U = np.real(ifft2(A_fft * K_fft))
    
    # 2. Growth function (Mapping neighborhood sum U to growth delta)
    G = bell(U, m, s) * 2.0 - 1.0
    
    # 3. Euler integration step
    A = np.clip(A + (1.0 / T) * G, 0.0, 1.0)
    
def draw():
    global A
    
    # Do a few physics steps per frame for smooth speed
    for _ in range(4):
        step_physics()
        
    py5.load_np_pixels()
    
    # Map State A [0,1] to colormap indices [0, 255]
    indices = (A * 255).astype(np.uint8)
    
    # Colors for the small WxH grid
    colors = colormap[indices] # Shape (H, W, 4)
    
    # Upscale by SCALE using Kronecker product or repeat
    # np.repeat is very fast
    upscaled = np.repeat(np.repeat(colors, SCALE, axis=0), SCALE, axis=1)
    
    # Write to py5 pixels
    # py5.np_pixels has shape (SIZE[1], SIZE[0], 4)
    py5.np_pixels[:] = upscaled
    
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
