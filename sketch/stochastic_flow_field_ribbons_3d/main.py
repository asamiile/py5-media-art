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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_RIBBONS = 2000
RIBBON_LENGTH = 30
NOISE_SCALE = 0.005
SPEED = 8.0

# Shape: (NUM_RIBBONS, RIBBON_LENGTH, 3)
ribbons = np.zeros((NUM_RIBBONS, RIBBON_LENGTH, 3), dtype=np.float32)

def init_ribbons():
    for i in range(NUM_RIBBONS):
        x = np.random.uniform(-SIZE[0]/2, SIZE[0]/2)
        y = np.random.uniform(-SIZE[1]/2, SIZE[1]/2)
        z = np.random.uniform(-500, 500)
        ribbons[i, :, 0] = x
        ribbons[i, :, 1] = y
        ribbons[i, :, 2] = z

def update_ribbons(t):
    # Shift histories back
    ribbons[:, 1:, :] = ribbons[:, :-1, :]
    
    # Update heads (index 0)
    heads = ribbons[:, 0, :]
    
    # We can't vectorize py5.os_noise easily for 2000 points without looping or writing a custom C/CUDA extension.
    # We'll use a fast numpy approximation of noise or just loop since 2000 isn't huge.
    
    # Let's try simple trig-based vector field as a substitute for 3D noise for performance
    x = heads[:, 0]
    y = heads[:, 1]
    z = heads[:, 2]
    
    # Complex vector field based on trig
    angle_x = np.sin(y * NOISE_SCALE + t) + np.cos(z * NOISE_SCALE * 1.5)
    angle_y = np.cos(x * NOISE_SCALE * 1.2 - t * 0.8) + np.sin(z * NOISE_SCALE)
    angle_z = np.sin(x * NOISE_SCALE - t) * np.cos(y * NOISE_SCALE)
    
    vx = angle_x * SPEED
    vy = angle_y * SPEED
    vz = angle_z * SPEED
    
    ribbons[:, 0, 0] += vx
    ribbons[:, 0, 1] += vy
    ribbons[:, 0, 2] += vz
    
    # Boundary wrap for heads (rough)
    heads_x = ribbons[:, 0, 0]
    heads_y = ribbons[:, 0, 1]
    heads_z = ribbons[:, 0, 2]
    
    bound_x = SIZE[0] * 0.8
    bound_y = SIZE[1] * 0.8
    bound_z = 800
    
    wrap_mask_x = np.abs(heads_x) > bound_x
    wrap_mask_y = np.abs(heads_y) > bound_y
    wrap_mask_z = np.abs(heads_z) > bound_z
    wrap_mask = wrap_mask_x | wrap_mask_y | wrap_mask_z
    
    # Reset completely if out of bounds
    if np.any(wrap_mask):
        ribbons[wrap_mask, :, 0] = np.random.uniform(-SIZE[0]/2, SIZE[0]/2, np.sum(wrap_mask))[:, None]
        ribbons[wrap_mask, :, 1] = np.random.uniform(-SIZE[1]/2, SIZE[1]/2, np.sum(wrap_mask))[:, None]
        ribbons[wrap_mask, :, 2] = np.random.uniform(-500, 500, np.sum(wrap_mask))[:, None]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    init_ribbons()
    py5.hint(py5.DISABLE_DEPTH_TEST) # Better additive blending
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 80, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    update_ribbons(t)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_y(t * 0.2)
    py5.rotate_x(t * 0.1)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(NUM_RIBBONS):
        hue = (180 + i * 0.1 + t * 20) % 360
        py5.stroke(hue, 80, 90, 40)
        
        py5.begin_shape()
        for j in range(RIBBON_LENGTH):
            p = ribbons[i, j]
            py5.vertex(p[0], p[1], p[2])
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
