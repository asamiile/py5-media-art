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

# Reaction-Diffusion constants
# Using a smaller grid for performance, scaled up during drawing
GRID_W, GRID_H = SIZE[0] // 4, SIZE[1] // 4
A = np.ones((GRID_H, GRID_W), dtype=np.float32)
B = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Seed initial pattern
cx, cy = GRID_W // 2, GRID_H // 2
# Add a few scattered seeds
for _ in range(20):
    rx, ry = np.random.randint(0, GRID_W), np.random.randint(0, GRID_H)
    A[ry-5:ry+5, rx-5:rx+5] = 0.5
    B[ry-5:ry+5, rx-5:rx+5] = 0.25

# Gray-Scott parameters for Coral-like growth
Da = 1.0
Db = 0.5
f = 0.0545
k = 0.0620
dt = 1.0

# Pre-calculate laplacian weights
weight_center = -1.0
weight_adj = 0.2
weight_diag = 0.05

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global A, B
    
    # We run multiple steps per frame to speed up the simulation visually
    steps_per_frame = 10
    
    # Slowly vary parameters to create dynamic changing patterns
    time_val = py5.frame_count * 0.005
    current_f = f + np.sin(time_val) * 0.002
    current_k = k + np.cos(time_val * 0.8) * 0.002
    
    for _ in range(steps_per_frame):
        # Compute Laplacian using roll for speed
        lap_A = (
            np.roll(A, 1, axis=0) * weight_adj +
            np.roll(A, -1, axis=0) * weight_adj +
            np.roll(A, 1, axis=1) * weight_adj +
            np.roll(A, -1, axis=1) * weight_adj +
            np.roll(np.roll(A, 1, axis=0), 1, axis=1) * weight_diag +
            np.roll(np.roll(A, 1, axis=0), -1, axis=1) * weight_diag +
            np.roll(np.roll(A, -1, axis=0), 1, axis=1) * weight_diag +
            np.roll(np.roll(A, -1, axis=0), -1, axis=1) * weight_diag +
            A * weight_center
        )
        
        lap_B = (
            np.roll(B, 1, axis=0) * weight_adj +
            np.roll(B, -1, axis=0) * weight_adj +
            np.roll(B, 1, axis=1) * weight_adj +
            np.roll(B, -1, axis=1) * weight_adj +
            np.roll(np.roll(B, 1, axis=0), 1, axis=1) * weight_diag +
            np.roll(np.roll(B, 1, axis=0), -1, axis=1) * weight_diag +
            np.roll(np.roll(B, -1, axis=0), 1, axis=1) * weight_diag +
            np.roll(np.roll(B, -1, axis=0), -1, axis=1) * weight_diag +
            B * weight_center
        )
        
        reaction = A * B * B
        
        next_A = A + (Da * lap_A - reaction + current_f * (1.0 - A)) * dt
        next_B = B + (Db * lap_B + reaction - (current_k + current_f) * B) * dt
        
        A = np.clip(next_A, 0.0, 1.0)
        B = np.clip(next_B, 0.0, 1.0)

    # Visualization
    # Create an RGB image from the concentrations
    img = py5.create_image(GRID_W, GRID_H, py5.RGB)
    
    # Map A and B to colors
    # We want a coral look: Deep teal background, bright coral pink/orange patterns
    # Calculate difference
    diff = (A - B) * 255.0
    
    # We can create a numpy array of pixel data and set it
    # py5 uses ARGB format integers for pixels in numpy
    img.load_np_pixels()
    
    # Create an ARGB array
    # A=255
    alpha = np.full((GRID_H, GRID_W), 255, dtype=np.uint32)
    
    # Color mapping
    # High B -> Coral (R=255, G=100, B=100)
    # High A -> Teal (R=0, G=150, B=200)
    
    # Normalized B [0, 1]
    norm_b = np.clip(B * 3.0, 0.0, 1.0)
    
    r = (norm_b * 255 + (1 - norm_b) * 0).astype(np.uint8)
    g = (norm_b * 100 + (1 - norm_b) * 150).astype(np.uint8)
    b_chan = (norm_b * 100 + (1 - norm_b) * 200).astype(np.uint8)
    
    # Assign to image channels (A, R, G, B)
    img.np_pixels[:, :, 0] = 255 # Alpha
    img.np_pixels[:, :, 1] = r
    img.np_pixels[:, :, 2] = g
    img.np_pixels[:, :, 3] = b_chan
    
    img.update_np_pixels()
    
    # Draw scaled image to screen
    py5.image(img, 0, 0, py5.width, py5.height)

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
