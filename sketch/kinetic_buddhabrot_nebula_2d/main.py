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

# Buddhabrot Parameters
NUM_PARTICLES = 3000000 # 1M per color channel
STEPS_PER_FRAME = 2

def spawn_c(num):
    # Random points in complex plane around Mandelbrot set
    # Real: -2.0 to 1.0, Imag: -1.5 to 1.5
    real = np.random.uniform(-2.2, 1.2, num).astype(np.float32)
    imag = np.random.uniform(-1.7, 1.7, num).astype(np.float32)
    return real + 1j * imag

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global Z, C_orig, age, max_age, colors
    
    Z = np.zeros(NUM_PARTICLES, dtype=np.complex64)
    C_orig = spawn_c(NUM_PARTICLES)
    age = np.zeros(NUM_PARTICLES, dtype=np.int32)
    
    # max_age sets the "frequency" of the nebula layers
    # Red: fast (broad nebula), Green: medium, Blue: slow (sharp details)
    max_age = np.zeros(NUM_PARTICLES, dtype=np.int32)
    N3 = NUM_PARTICLES // 3
    max_age[:N3] = 30       # Red
    max_age[N3:2*N3] = 80   # Green
    max_age[2*N3:] = 200    # Blue
    
    colors = np.zeros((NUM_PARTICLES, 3), dtype=np.uint8)
    # R
    colors[:N3, 0] = 60
    colors[:N3, 1] = 10
    colors[:N3, 2] = 5
    # G
    colors[N3:2*N3, 0] = 5
    colors[N3:2*N3, 1] = 50
    colors[N3:2*N3, 2] = 20
    # B
    colors[2*N3:, 0] = 10
    colors[2*N3:, 1] = 20
    colors[2*N3:, 2] = 70

def step_physics(t):
    global Z, C_orig, age
    
    # Slowly rotate the fractal's parameter space
    # C(t) = C_orig * e^{i * t} + slight translation
    rot = np.exp(1j * t)
    C = C_orig * rot + (np.sin(t*0.5)*0.1 + 1j*np.cos(t*0.3)*0.1)
    
    # Iterate
    Z = Z**2 + C
    age += 1
    
    # Escaped or died of old age
    # Note: absolute value of complex is np.abs(Z). We use Z.real**2 + Z.imag**2 > 4 for speed
    escaped = (Z.real * Z.real + Z.imag * Z.imag > 4.0) | (age > max_age)
    
    # Respawn
    num_escaped = np.sum(escaped)
    if num_escaped > 0:
        Z[escaped] = 0.0 + 0.0j
        C_orig[escaped] = spawn_c(num_escaped)
        age[escaped] = 0

def draw():
    global Z
    
    t = py5.frame_count * 0.005
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / deep space fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 230 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # Map complex plane to screen
    # Real [-2.5, 1.5] -> X [0, W]
    # Imag [-1.5, 1.5] -> Y [H, 0]
    scale = H / 3.0
    cx = W / 2.0 + 0.5 * scale
    cy = H / 2.0
    
    # To get a nice rotation on screen, we can rotate Z itself before plotting
    # or just let C rotation do the work (C rotation naturally rotates the fractal).
    screen_x = (Z.real * scale + cx).astype(np.int32)
    screen_y = (Z.imag * scale + cy).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    vr = colors[valid, 0]
    vg = colors[valid, 1]
    vb = colors[valid, 2]
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    flat_pixels[flat_indices, 1] = np.clip(flat_pixels[flat_indices, 1].astype(np.uint16) + vr, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 2] = np.clip(flat_pixels[flat_indices, 2].astype(np.uint16) + vg, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 3] = np.clip(flat_pixels[flat_indices, 3].astype(np.uint16) + vb, 0, 255).astype(np.uint8)
    
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
