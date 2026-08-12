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

# Grid parameters
GRID_W = SIZE[0] // 2  # Render at half resolution then upscale for performance and smooth textures
GRID_H = SIZE[1] // 2

# Coupled Map Lattice state
# We use float32 grids
state = np.random.rand(GRID_H, GRID_W).astype(np.float32)
r_param = 3.92  # Chaotic regime parameter for logistic map
epsilon = 0.25  # Coupling constant

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def update_cml():
    global state
    # f(x) = r * x * (1 - x)
    mapped = r_param * state * (1.0 - state)
    
    # Spatial diffusion (4-neighbor average with wrapping)
    left = np.roll(mapped, 1, axis=1)
    right = np.roll(mapped, -1, axis=1)
    up = np.roll(mapped, 1, axis=0)
    down = np.roll(mapped, -1, axis=0)
    
    neighbor_avg = 0.25 * (left + right + up + down)
    
    # State update: (1 - epsilon) * f(x) + epsilon * neighbor_avg
    state = (1.0 - epsilon) * mapped + epsilon * neighbor_avg
    # Clamping state between 0 and 1 to prevent runaway values
    state = np.clip(state, 0.0, 1.0)

def draw():
    update_cml()
    
    # Create the visual frame
    # We map state to colors using a custom shader-like NumPy mapping.
    # Dominant (60%): Deep Amethyst Purple
    # Secondary (30%): Luminous Cyan
    # Accent (10%): Solar Gold
    
    # We will generate RGB channels based on the state and its local gradient
    # Gradient magnitude shows the boundaries
    left = np.roll(state, 1, axis=1)
    right = np.roll(state, -1, axis=1)
    up = np.roll(state, 1, axis=0)
    down = np.roll(state, -1, axis=0)
    
    grad_x = 0.5 * (right - left)
    grad_y = 0.5 * (down - up)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    grad_mag = np.clip(grad_mag * 5.0, 0.0, 1.0) # Boost contrast of boundaries
    
    # Color calculations (0 to 255)
    # Background / Deep Amethyst: state * 0.3 (r), state * 0.1 (g), state * 0.5 (b)
    # Luminous Cyan on high state: state * 0.1 (r), state * 0.8 (g), state * 0.9 (b)
    # Solar Gold on boundaries: grad_mag * 1.0 (r), grad_mag * 0.75 (g), grad_mag * 0.1 (b)
    
    # We mix these components
    r = (state * 0.2 + (1.0 - state) * 0.05 + grad_mag * 0.9) * 255
    g = (state * 0.1 + (1.0 - state) * 0.4 + grad_mag * 0.7) * 255
    b = (state * 0.6 + (1.0 - state) * 0.6 + grad_mag * 0.1) * 255
    
    # Convert to 4-channel uint8 array matching img.np_pixels shape (GRID_H, GRID_W, 4)
    # in py5, channels are: 0=Alpha, 1=Red, 2=Green, 3=Blue
    img_data = np.zeros((GRID_H, GRID_W, 4), dtype=np.uint8)
    img_data[:, :, 0] = 255  # Alpha
    img_data[:, :, 1] = np.clip(r, 0, 255).astype(np.uint8)
    img_data[:, :, 2] = np.clip(g, 0, 255).astype(np.uint8)
    img_data[:, :, 3] = np.clip(b, 0, 255).astype(np.uint8)
    
    # Create py5 image from grid and upscale to screen size
    img = py5.create_image(GRID_W, GRID_H, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:] = img_data
    img.update_pixels()
    
    # Draw image scaled up to screen resolution with bilinear filtering
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
