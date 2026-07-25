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

# Grid size for Double Pendulum Fractal
SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

STEPS_PER_FRAME = 3
DT = 0.05
G = 1.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global th1, th2, w1, w2, colormap
    
    # Initialize phases based on screen coordinates
    # Map X to theta1 [-PI, PI]
    # Map Y to theta2 [-PI, PI]
    y, x = np.ogrid[0:H, 0:W]
    
    # We zoom in on a highly chaotic region: theta1 in [1.0, 2.0], theta2 in [1.0, 2.0]
    th1 = (x / float(W) * 1.0 + 1.0).astype(np.float32)
    th1 = np.repeat(th1, H, axis=0)
    
    th2 = (y / float(H) * 1.0 + 1.0).astype(np.float32)
    th2 = np.repeat(th2, W, axis=1)
    
    w1 = np.zeros((H, W), dtype=np.float32)
    w2 = np.zeros((H, W), dtype=np.float32)
    
    # Pre-generate an intense neon colormap (Psychedelic thermal map)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        hue = (i / 255.0 + 0.5) % 1.0
        # Convert HSB to RGB (S=1.0, B=1.0)
        h_idx = hue * 6.0
        c = 1.0
        x_c = c * (1 - abs(h_idx % 2 - 1))
        
        if h_idx < 1: r, g, b = c, x_c, 0
        elif h_idx < 2: r, g, b = x_c, c, 0
        elif h_idx < 3: r, g, b = 0, c, x_c
        elif h_idx < 4: r, g, b = 0, x_c, c
        elif h_idx < 5: r, g, b = x_c, 0, c
        else: r, g, b = c, 0, x_c
            
        colormap[i, 0] = 255 # Alpha
        colormap[i, 1] = int(r * 255)
        colormap[i, 2] = int(g * 255)
        colormap[i, 3] = int(b * 255)

def step_physics():
    global th1, th2, w1, w2
    
    # Vectorized Double Pendulum Equations (m1=m2=1, L1=L2=1)
    delta = th1 - th2
    
    sin_delta = np.sin(delta)
    cos_delta = np.cos(delta)
    sin_th1 = np.sin(th1)
    
    denom = 2.0 - cos_delta * cos_delta
    denom = np.where(denom < 0.001, 0.001, denom)
    
    # Accelerations
    num1 = -G * (2.0 * sin_th1) - G * np.sin(th1 - 2.0 * th2) - 2.0 * sin_delta * (w2 * w2 + w1 * w1 * cos_delta)
    a1 = num1 / denom
    
    num2 = 2.0 * sin_delta * (w1 * w1 * 2.0 + G * (2.0 * np.cos(th1)) + w2 * w2 * cos_delta)
    a2 = num2 / denom
    
    # Symplectic Euler integration
    w1 += a1 * DT
    w2 += a2 * DT
    
    # Slight damping to prevent numerical explosion
    w1 *= 0.999
    w2 *= 0.999
    
    th1 += w1 * DT
    th2 += w2 * DT

def draw():
    global th1, th2, w1, w2
    
    for _ in range(STEPS_PER_FRAME):
        step_physics()
        
    py5.load_np_pixels()
    
    # Map theta2 to hue (wrap around PI)
    norm_th2 = ((th2 + py5.frame_count * 0.01) % py5.TWO_PI) / py5.TWO_PI
    color_indices = (norm_th2 * 255).astype(np.uint8)
    
    img_data = colormap[color_indices]
    
    # Scale up
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
