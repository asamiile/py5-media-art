from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import cv2
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

# Simulation grid (Run at a lower resolution, then upscale for speed)
Nx, Ny = 384, 216
dx = 1.0
D = 0.15 # Diffusion coefficient
dt = 0.1

# Parameters for unstable symmetric fixed point (produces stable spiral waves)
alpha = 1.8
beta = 0.4

# State variables
s1 = None
s2 = None
s3 = None

def init_simulation():
    global s1, s2, s3
    s_eq = 1.0 / (1.0 + alpha + beta)
    
    # Base symmetric state
    s1 = np.ones((Nx, Ny)) * s_eq
    s2 = np.ones((Nx, Ny)) * s_eq
    s3 = np.ones((Nx, Ny)) * s_eq
    
    # Partition the grid into multiple randomly seeded circular regions to generate diverse spiral centers
    X, Y = np.meshgrid(np.arange(Nx), np.arange(Ny), indexing='ij')
    
    np.random.seed(random.randint(0, 10000))
    for _ in range(8):
        cx = random.randint(20, Nx-20)
        cy = random.randint(20, Ny-20)
        r = random.randint(25, 50)
        mask = (X - cx)**2 + (Y - cy)**2 < r**2
        
        # Randomly choose one species to dominate in this patch
        choice = random.choice([1, 2, 3])
        if choice == 1:
            s1[mask] += 0.35
            s2[mask] -= 0.15
            s3[mask] -= 0.15
        elif choice == 2:
            s2[mask] += 0.35
            s1[mask] -= 0.15
            s3[mask] -= 0.15
        else:
            s3[mask] += 0.35
            s1[mask] -= 0.15
            s2[mask] -= 0.15

    # Add random fine-scale noise
    s1 += np.random.normal(0, 0.03, size=(Nx, Ny))
    s2 += np.random.normal(0, 0.03, size=(Nx, Ny))
    s3 += np.random.normal(0, 0.03, size=(Nx, Ny))
    
    # Clip to physical limits
    s1 = np.clip(s1, 0.0, 1.5)
    s2 = np.clip(s2, 0.0, 1.5)
    s3 = np.clip(s3, 0.0, 1.5)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    init_simulation()

def laplacian(u):
    return (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u) / (dx**2)

def step_simulation():
    global s1, s2, s3
    
    # Run multiple micro-steps per frame to speed up the dynamics
    for _ in range(3):
        ds1 = s1 * (1.0 - s1 - alpha * s2 - beta * s3) + D * laplacian(s1)
        ds2 = s2 * (1.0 - s2 - alpha * s3 - beta * s1) + D * laplacian(s2)
        ds3 = s3 * (1.0 - s3 - alpha * s1 - beta * s2) + D * laplacian(s3)
        
        s1 += dt * ds1
        s2 += dt * ds2
        s3 += dt * ds3
        
        s1 = np.clip(s1, 0.0, 1.5)
        s2 = np.clip(s2, 0.0, 1.5)
        s3 = np.clip(s3, 0.0, 1.5)

def draw():
    step_simulation()

    # Get render buffer dimensions
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    # Colors
    color_bg = np.array([5, 5, 10]) / 255.0
    color_magenta = np.array([255, 0, 127]) / 255.0
    color_cyan = np.array([0, 229, 255]) / 255.0
    color_amber = np.array([255, 179, 0]) / 255.0

    # Color field blending
    total_s = s1 + s2 + s3
    bg_factor = np.clip(1.0 - total_s, 0, 1)

    rgb = np.zeros((Nx, Ny, 3))
    rgb += bg_factor[..., None] * color_bg
    rgb += s1[..., None] * color_magenta
    rgb += s2[..., None] * color_cyan
    rgb += s3[..., None] * color_amber

    # Calculate active border outlines using Laplacian
    edge = laplacian(s1)**2 + laplacian(s2)**2 + laplacian(s3)**2
    edge = np.clip(edge * 60.0, 0, 1)

    # Blend edge glow
    rgb = rgb * (1.0 - edge[..., None] * 0.5) + edge[..., None] * np.array([1.0, 1.0, 1.0])

    rgb_uint8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)

    # Resize to screen resolution
    rgb_resized = cv2.resize(rgb_uint8, (w, h), interpolation=cv2.INTER_LINEAR)

    # Set pixel buffer
    py5.np_pixels[:, :, :3] = rgb_resized
    py5.np_pixels[:, :, 3] = 255
    py5.update_np_pixels()

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if blank screen
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels[:, :, :3].std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # End sketch and build video
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
