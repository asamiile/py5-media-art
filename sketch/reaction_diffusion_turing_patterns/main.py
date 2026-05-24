from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation size (downscaled slightly for performance, upscaled during render if needed)
# Since we are rendering directly to np_pixels, we use SIZE.
# But 1920x1080 reaction diffusion is too slow for 60fps in pure python.
# We will simulate at 480x270 and upscale.
SIM_W = SIZE[0] // 4
SIM_H = SIZE[1] // 4

# Gray-Scott parameters
Du = 1.0
Dv = 0.5
feed = 0.055
kill = 0.062
dt = 1.0

# Grids
u = np.ones((SIM_H, SIM_W), dtype=np.float32)
v = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Laplacian kernel
kernel = np.array([[0.05, 0.2, 0.05],
                   [0.2, -1.0, 0.2],
                   [0.05, 0.2, 0.05]], dtype=np.float32)

def setup():
    global u, v
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed initial "v" chemical
    # Drop some squares
    for _ in range(20):
        rx = np.random.randint(10, SIM_W - 10)
        ry = np.random.randint(10, SIM_H - 10)
        u[ry:ry+10, rx:rx+10] = 0.5
        v[ry:ry+10, rx:rx+10] = 0.25
        
    # Add noise to seed
    v += np.random.random((SIM_H, SIM_W)) * 0.1
    py5.background(0)

def draw():
    global u, v, feed, kill
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Modulate feed and kill rates to transition between different Turing patterns
    # (spots -> stripes -> labyrinth)
    current_feed = py5.lerp(0.054, 0.030, t)
    current_kill = py5.lerp(0.062, 0.060, t)
    
    # Run multiple physics steps per frame for speed
    for _ in range(8):
        lap_u = convolve(u, kernel, mode='wrap')
        lap_v = convolve(v, kernel, mode='wrap')
        
        uvv = u * v * v
        
        du = Du * lap_u - uvv + current_feed * (1.0 - u)
        dv = Dv * lap_v + uvv - (current_feed + current_kill) * v
        
        u += du * dt
        v += dv * dt
        
    # v ranges roughly 0 to 1, mostly around 0.0 to 0.4
    # Map to colors
    # We will use nearest neighbor upscaling to full SIZE for the pixel buffer
    v_norm = np.clip(v * 3.0, 0.0, 1.0)
    
    # Upscale
    v_up = np.kron(v_norm, np.ones((4, 4), dtype=np.float32))
    
    # We want exact bounds matching
    v_up = v_up[:SIZE[1], :SIZE[0]]
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Color palette
    # Deep Purple background: 30, 0, 50
    # Cyan foreground: 0, 255, 255
    # Neon Orange highlights: 255, 100, 0
    
    r = (30 * (1-v_up) + 0 * (v_up < 0.5) * v_up*2 + 255 * (v_up >= 0.5)).astype(np.uint8)
    g = (0 * (1-v_up) + 255 * (v_up < 0.5) * v_up*2 + 100 * (v_up >= 0.5)).astype(np.uint8)
    b = (50 * (1-v_up) + 255 * (v_up < 0.5) * v_up*2 + 0 * (v_up >= 0.5)).astype(np.uint8)
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = r
    pixels[:, :, 2] = g
    pixels[:, :, 3] = b
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
