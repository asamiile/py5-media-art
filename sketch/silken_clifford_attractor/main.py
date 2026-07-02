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
W, H = SIZE

# We will compute the attractor in batches
BATCH_SIZE = 1000000
STEPS_PER_FRAME = 6

# Initial state for batch
x = np.random.uniform(-1, 1, BATCH_SIZE).astype(np.float32)
y = np.random.uniform(-1, 1, BATCH_SIZE).astype(np.float32)

# Colormap
def tone_map(density):
    # density is normalized
    # Map to Black -> Indigo -> Crimson -> Gold -> White
    
    r = np.zeros_like(density)
    g = np.zeros_like(density)
    b = np.zeros_like(density)
    
    # Indigo (75, 0, 130) at low density
    # Crimson (220, 20, 60) at mid density
    # Gold (255, 215, 0) at high density
    
    # 0.0 to 0.1: Black to Indigo
    m1 = density < 0.1
    r[m1] = density[m1] * 10 * 75
    g[m1] = 0
    b[m1] = density[m1] * 10 * 130
    
    # 0.1 to 0.4: Indigo to Crimson
    m2 = (density >= 0.1) & (density < 0.4)
    t2 = (density[m2] - 0.1) / 0.3
    r[m2] = 75 + t2 * (220 - 75)
    g[m2] = 0 + t2 * (20 - 0)
    b[m2] = 130 + t2 * (60 - 130)
    
    # 0.4 to 0.8: Crimson to Gold
    m3 = (density >= 0.4) & (density < 0.8)
    t3 = (density[m3] - 0.4) / 0.4
    r[m3] = 220 + t3 * (255 - 220)
    g[m3] = 20 + t3 * (215 - 20)
    b[m3] = 60 + t3 * (0 - 60)
    
    # 0.8 to 1.0+: Gold to White
    m4 = density >= 0.8
    t4 = np.clip((density[m4] - 0.8) / 0.2, 0, 1)
    r[m4] = 255
    g[m4] = 215 + t4 * (255 - 215)
    b[m4] = t4 * 255
    
    return np.clip(r, 0, 255).astype(np.uint8), np.clip(g, 0, 255).astype(np.uint8), np.clip(b, 0, 255).astype(np.uint8)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global x, y
    
    t = py5.frame_count * 0.005
    
    # Slowly drifting parameters
    a = 1.4 + 0.2 * np.sin(t * 1.3)
    b = -1.2 + 0.3 * np.cos(t * 0.8)
    c = 1.5 + 0.1 * np.sin(t * 2.1)
    d = -1.1 + 0.2 * np.cos(t * 1.5)
    
    buffer = np.zeros((H, W), dtype=np.uint32)
    
    # Run iterations
    for _ in range(STEPS_PER_FRAME):
        # Clifford attractor equations
        x_new = np.sin(a * y) + c * np.cos(a * x)
        y_new = np.sin(b * x) + d * np.cos(b * y)
        x[:] = x_new
        y[:] = y_new
        
        # Map coordinates to screen (typically x,y are in [-abs(c)-1, abs(c)+1])
        # We assume range roughly [-2.5, 2.5]
        scale = H / 5.5
        sx = (x * scale + W / 2).astype(np.int32)
        sy = (y * scale + H / 2).astype(np.int32)
        
        # Filter bounds
        valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
        sx = sx[valid]
        sy = sy[valid]
        
        # Accumulate density
        flat_idx = sy * W + sx
        counts = np.bincount(flat_idx, minlength=W*H)
        buffer += counts.astype(np.uint32).reshape((H, W))
        
    # Tone mapping with gamma correction
    buffer_float = buffer.astype(np.float32)
    max_val = np.percentile(buffer_float[buffer_float > 0], 99.95) if np.any(buffer_float > 0) else 1.0
    max_val = max(max_val, 1.0)
    
    # Non-linear scaling (gamma)
    density = np.power(buffer_float / max_val, 0.6)
    
    r, g, b_col = tone_map(density)
    
    alpha = np.full((H, W, 1), 255, dtype=np.uint8)
    rgb = np.stack((r, g, b_col), axis=-1)
    argb = np.concatenate((alpha, rgb), axis=-1)
    
    py5.load_np_pixels()
    py5.np_pixels[:] = argb
    py5.update_np_pixels()
    
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
