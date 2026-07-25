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

# Simulation state
MAX_ITER = 50
N_SAMPLES = 100000 # Samples per frame

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def generate_buddhabrot_paths(shift_c):
    # Random points in complex plane [-2, 2] + [-2, 2]j
    c = np.random.uniform(-2, 2, N_SAMPLES) + 1j * np.random.uniform(-2, 2, N_SAMPLES)
    c += shift_c
    
    z = np.zeros_like(c, dtype=np.complex64)
    c_cast = c.astype(np.complex64)
    
    paths = []
    escaped = np.zeros(N_SAMPLES, dtype=bool)
    
    # Iterate
    for i in range(MAX_ITER):
        # Only iterate points that haven't escaped yet (optimization)
        active = ~escaped
        z[active] = z[active]**2 + c_cast[active]
        paths.append(z.copy())
        
        # Check escape condition
        escaped[active] = np.abs(z[active]) > 2.0
    
    # We only plot paths for points that EVENTUALLY escaped
    # Convert paths to a big array
    paths_array = np.array(paths) # Shape: (MAX_ITER, N_SAMPLES)
    
    # Filter only escaped columns
    escaped_paths = paths_array[:, escaped] # Shape: (MAX_ITER, N_escaped)
    
    # Flatten
    all_z = escaped_paths.flatten()
    
    return all_z

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Modulate a shift to 'c' to animate through the 4D fractal space
    shift_c = 0.2 * np.sin(t) + 1j * 0.2 * np.cos(t * 1.5)
    
    all_z = generate_buddhabrot_paths(shift_c)
    
    # Map to screen
    screen_x = (all_z.real + 2.0) / 4.0 * SIZE[0]
    screen_y = (all_z.imag + 2.0) / 4.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Deep Nebula Purple, Fiery Orange, and Luminous White
    density_norm = np.clip(density_buffer / 50.0, 0, 1)
    
    r = 255 * (density_norm ** 1.5)
    g = 150 * (density_norm ** 2.0)
    b = 255 * (density_norm ** 0.8)
    
    # Add fiery orange highlights
    orange_mask = density_norm > 0.5
    r[orange_mask] = 255
    g[orange_mask] = 100 + 155 * ((density_norm[orange_mask] - 0.5) / 0.5)
    b[orange_mask] = 255 - 200 * ((density_norm[orange_mask] - 0.5) / 0.5)
    
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r.astype(np.uint8)
    py5.np_pixels[:, :, 2] = g.astype(np.uint8)
    py5.np_pixels[:, :, 3] = b.astype(np.uint8)
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
