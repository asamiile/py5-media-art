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
DURATION_SEC = random.randint(15, 20)  # Dynamic duration: 15-20 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Downscaled grid for optimal 60fps performance
SIM_W = 960
SIM_H = 540

# PDE Parameters
DT = 0.04
STEPS_PER_FRAME = 4

# Scalar field state
u = None

def setup():
    global u
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize with small random fluctuations around zero state
    u = np.random.uniform(-0.1, 0.1, (SIM_H, SIM_W)).astype(np.float32)


def laplacian(grid):
    # Fast 5-point discrete Laplacian with wrapping boundaries
    return (
        np.roll(grid, 1, axis=0) +
        np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) +
        np.roll(grid, -1, axis=1) -
        4.0 * grid
    )


def draw():
    global u

    # Generate space-time parameter r
    t = py5.frame_count * 0.005
    
    # Generate a slow spatially varying control field r using grid coords & sine waves
    # This creates dynamic transitions between stripes and spots across the canvas
    ys, xs = np.ogrid[:SIM_H, :SIM_W]
    r = 0.05 + 0.12 * np.sin(xs * 0.006 + t) * np.cos(ys * 0.008 - t * 0.5)

    # Solve the Swift-Hohenberg PDE:
    # du/dt = (r - 1)*u - 2*Laplacian(u) - Biharmonic(u) - u^3
    for _ in range(STEPS_PER_FRAME):
        lap = laplacian(u)
        biharmonic = laplacian(lap)
        
        # PDE update
        u_next = u + DT * ((r - 1.0) * u - 2.0 * lap - biharmonic - u**3)
        # Prevent runaway instability
        u = np.clip(u_next, -2.0, 2.0)

    # Map the u field (values typically range [-1.0, 1.0]) to colors
    # Obsidian Void: black background where u is near 0
    # Ocean Teal: where u is negative (ridges/troughs)
    # Coral Sienna: where u is positive (peaks)
    # Neon Gold: where u has high absolute values (intense ridges)

    # Normalize u to [0, 1] range for color mapping
    u_norm = (u + 1.0) * 0.5
    u_norm = np.clip(u_norm, 0.0, 1.0)

    r_field = np.zeros_like(u)
    g_field = np.zeros_like(u)
    b_field = np.zeros_like(u)

    # Mapping negative values (u < 0, u_norm < 0.5) to Ocean Teal (10, 110, 130)
    mask_neg = u_norm < 0.5
    t_neg = u_norm[mask_neg] / 0.5
    r_field[mask_neg] = t_neg * 10
    g_field[mask_neg] = t_neg * 110
    b_field[mask_neg] = t_neg * 130

    # Mapping positive values (u >= 0, u_norm >= 0.5) to Coral Sienna (210, 80, 50)
    mask_pos = u_norm >= 0.5
    t_pos = (u_norm[mask_pos] - 0.5) / 0.5
    r_field[mask_pos] = t_pos * 210
    g_field[mask_pos] = t_pos * 80
    b_field[mask_pos] = t_pos * 50

    # Map extremely high amplitudes to Neon Gold (255, 215, 0)
    high_amp = np.abs(u) > 0.6
    amp_factor = np.clip((np.abs(u[high_amp]) - 0.6) / 0.4, 0.0, 1.0)
    r_field[high_amp] = r_field[high_amp] * (1.0 - amp_factor) + 255 * amp_factor
    g_field[high_amp] = g_field[high_amp] * (1.0 - amp_factor) + 215 * amp_factor
    b_field[high_amp] = b_field[high_amp] * (1.0 - amp_factor) + 0 * amp_factor

    # Convert to ARGB format
    r_int = np.clip(r_field, 0, 255).astype(np.uint8)
    g_int = np.clip(g_field, 0, 255).astype(np.uint8)
    b_int = np.clip(b_field, 0, 255).astype(np.uint8)
    a_int = np.full_like(r_int, 255)

    # Load upscaled version using Py5Image
    img = py5.create_image(SIM_W, SIM_H, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:, :, 0] = a_int
    img.np_pixels[:, :, 1] = r_int
    img.np_pixels[:, :, 2] = g_int
    img.np_pixels[:, :, 3] = b_int
    img.update_np_pixels()

    # Draw to screen with bilinear scaling
    py5.image(img, 0, 0, *SIZE)

    # Save the frame
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

    # Complete render
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
