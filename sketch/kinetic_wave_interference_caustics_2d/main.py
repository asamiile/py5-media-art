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

# Simulation Grid (Wave Equation)
SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

STEPS_PER_FRAME = 4
DAMPING = 0.999

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global u, u_old, c2, colormap, x, y
    
    u = np.zeros((H, W), dtype=np.float32)
    u_old = np.zeros((H, W), dtype=np.float32)
    
    y, x = np.ogrid[0:H, 0:W]
    
    # Wave speed c(x,y) squared. This acts as the refractive index.
    # We use a mix of low-frequency sines to create "lenses"
    c_val = 0.4 + 0.15 * np.sin(x * 0.015) * np.cos(y * 0.01) + 0.15 * np.cos(x * 0.007 + y * 0.012)
    c_val = np.clip(c_val, 0.1, 0.6) # c must be < 0.707 for 2D stability on a 3x3 grid
    c2 = c_val * c_val
    
    # Pre-generate a Caustic Water colormap (Deep Blue -> Cyan -> White)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = (i - 128) / 128.0 # Range [-1, 1]
        
        colormap[i, 0] = 255 # Alpha
        
        if v < -0.1:
            # Negative peaks (Troughs) - Deep Blue to Black
            p = (v + 1.0) / 0.9
            colormap[i, 1:] = [0, int(30 * p), int(80 * p)]
        elif v < 0.1:
            # Zero crossing - Deep Blue to Cyan
            p = (v + 0.1) / 0.2
            colormap[i, 1:] = [0, 30 + int(70 * p), 80 + int(100 * p)]
        elif v < 0.6:
            # Positive peaks - Cyan to Bright Cyan
            p = (v - 0.1) / 0.5
            colormap[i, 1:] = [0, 100 + int(100 * p), 180 + int(75 * p)]
        else:
            # High peaks - Bright Cyan to White (Caustics)
            p = (v - 0.6) / 0.4
            colormap[i, 1:] = [int(255 * p), 200 + int(55 * p), 255]

def step_physics(t):
    global u, u_old
    
    # Laplacian using 9-point stencil for isotropy and stability
    cross = np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1)
    diag = np.roll(np.roll(u, 1, 0), 1, 1) + np.roll(np.roll(u, -1, 0), -1, 1) + \
           np.roll(np.roll(u, 1, 0), -1, 1) + np.roll(np.roll(u, -1, 0), 1, 1)
           
    laplacian = cross * 0.2 + diag * 0.05 - u
    
    # Verlet integration for wave equation
    u_new = 2.0 * u - u_old + c2 * laplacian
    
    # Inject ripples from moving emitters
    # 5 emitters moving in Lissajous orbits
    for i in range(5):
        ex = int(W/2 + W*0.3 * np.sin(t * (1.1 + i*0.2) + i))
        ey = int(H/2 + H*0.3 * np.cos(t * (1.3 + i*0.17) - i))
        
        ex = np.clip(ex, 2, W-3)
        ey = np.clip(ey, 2, H-3)
        
        # Inject an oscillating wave
        u_new[ey-2:ey+3, ex-2:ex+3] += np.sin(t * 10.0 + i) * 2.5
    
    # Update states
    u_old[:] = u
    u[:] = u_new * DAMPING

def draw():
    global u
    
    t = py5.frame_count * 0.016
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        t += 0.005 # internal time step
        
    py5.load_np_pixels()
    
    # Map wave amplitude [-2, 2] to [0, 255] color indices
    # We use a non-linear mapping (e.g. sinh or just scaling) to emphasize sharp peaks
    u_scaled = np.clip(u * 64 + 128, 0, 255).astype(np.uint8)
    
    img_data = colormap[u_scaled]
    
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
