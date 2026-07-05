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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle system
N_PARTICLES = 150000
x = np.random.uniform(-3, 3, N_PARTICLES).astype(np.float32)
y = np.random.uniform(-3, 3, N_PARTICLES).astype(np.float32)

# Clifford attractor params
# a, b, c, d
params_start = np.array([1.4, 1.56, 1.4, -6.56])
params_end = np.array([-1.7, 1.3, -0.1, -1.2])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global x, y
    
    # Trails fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 8, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Interpolate parameters
    progress = py5.frame_count / TOTAL_FRAMES
    # Smoothstep interpolation
    progress = progress * progress * (3 - 2 * progress)
    
    p = params_start + (params_end - params_start) * progress
    a, b, c, d = p
    
    # Clifford Attractor step
    x_new = np.sin(a * y) + c * np.cos(a * x)
    y_new = np.sin(b * x) + d * np.cos(b * y)
    
    x[:] = x_new
    y[:] = y_new
    
    # Map to screen
    scale = SIZE[1] * 0.18
    screen_x = x * scale + SIZE[0] / 2
    screen_y = y * scale + SIZE[1] / 2
    
    # Fast rendering
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1)
    
    r_val = int(50 + progress * 100)
    g_val = int(200 - progress * 100)
    b_val = 255
    py5.stroke(r_val, g_val, b_val, 120)
    
    py5.begin_shape(py5.POINTS)
    for i in range(N_PARTICLES):
        py5.vertex(screen_x[i], screen_y[i])
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
