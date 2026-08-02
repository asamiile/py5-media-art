from pathlib import Path
import random
import shutil
import subprocess
import sys
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
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Grid parameters for offscreen simulation
GRID_SIZE = 256

# Lenia parameters (Orbium Preset)
R = 13.0
dt = 0.1
mu = 0.15
sigma = 0.015

# Global simulation state
A = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
K_fft = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.complex64)
img_buffer = None

def build_kernel(r, size):
    """Build normalized annular kernel in the frequency domain."""
    y, x = np.ogrid[-size // 2 : size // 2, -size // 2 : size // 2]
    dist = np.sqrt(x * x + y * y) / r
    # Bell-shaped kernel: peaks at dist=0.5
    kernel = np.exp(-((dist - 0.5) ** 2) / (2.0 * 0.15**2)) * (dist < 1.0)
    kernel = kernel / (kernel.sum() + 1e-10)
    return np.fft.fft2(np.fft.fftshift(kernel)).astype(np.complex64)

def growth_fn(u, mu_val, sigma_val):
    """Bell-shaped Lenia growth mapping function."""
    return 2.0 * np.exp(-((u - mu_val) ** 2) / (2.0 * sigma_val**2)) - 1.0

def initialize_grid(size):
    """Seed multiple overlapping spots in the center to initiate glider structures."""
    a = np.zeros((size, size), dtype=np.float32)
    c = size // 2
    # Place 6 localized random patches of activity
    for _ in range(6):
        sx = c + random.randint(-18, 18)
        sy = c + random.randint(-18, 18)
        radius = random.randint(7, 13)
        for y in range(max(0, sy - radius), min(size, sy + radius + 1)):
            for x in range(max(0, sx - radius), min(size, sx + radius + 1)):
                if (x - sx) ** 2 + (y - sy) ** 2 <= radius**2:
                    a[y, x] = random.uniform(0.18, 0.95)
    return a

def setup():
    global A, K_fft, img_buffer
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Lenia kernel and activity grids
    random.seed(random.randint(0, 999999))
    K_fft = build_kernel(R, GRID_SIZE)
    A = initialize_grid(GRID_SIZE)
    
    # Initialize offscreen image buffer
    img_buffer = py5.create_image(GRID_SIZE, GRID_SIZE, py5.ARGB)

def draw():
    global A
    fc = py5.frame_count
    
    # 1. Update Lenia Simulation step in frequency domain
    A_fft = np.fft.fft2(A)
    potential = np.real(np.fft.ifft2(K_fft * A_fft)).astype(np.float32)
    growth = growth_fn(potential, mu, sigma)
    
    # Update grid
    next_A = np.clip(A + dt * growth, 0.0, 1.0)
    
    # Wither/decay during final phase for a clean loop transition back to dark void
    if fc > 780:
        decay_factor = py5.remap(fc, 780, 900, 1.0, 0.88)
        A = next_A * decay_factor
    else:
        A = next_A

    # 2. Vectorized Color Mapping (Dark purple void -> Electric Violet -> Cyan -> Amber Gold)
    color_r = np.zeros_like(A)
    color_g = np.zeros_like(A)
    color_b = np.zeros_like(A)
    
    # Range 0.0 to 0.35: void [8, 4, 16] to electric violet [90, 0, 255]
    m1 = A <= 0.35
    t1 = A / 0.35
    color_r[m1] = 8 + t1[m1] * (90 - 8)
    color_g[m1] = 4 + t1[m1] * (0 - 4)
    color_b[m1] = 16 + t1[m1] * (255 - 16)
    
    # Range 0.35 to 0.75: electric violet [90, 0, 255] to cyan [0, 240, 255]
    m2 = (A > 0.35) & (A <= 0.75)
    t2 = (A - 0.35) / 0.40
    color_r[m2] = 90 + t2[m2] * (0 - 90)
    color_g[m2] = 0 + t2[m2] * (240 - 0)
    color_b[m2] = 255 + t2[m2] * (255 - 255)
    
    # Range 0.75 to 1.0: cyan [0, 240, 255] to amber gold [255, 185, 0]
    m3 = A > 0.75
    t3 = (A - 0.75) / 0.25
    color_r[m3] = 0 + t3[m3] * (255 - 0)
    color_g[m3] = 240 + t3[m3] * (185 - 240)
    color_b[m3] = 255 + t3[m3] * (0 - 255)
    
    color_r = np.clip(color_r, 0, 255).astype(np.int32)
    color_g = np.clip(color_g, 0, 255).astype(np.int32)
    color_b = np.clip(color_b, 0, 255).astype(np.int32)
    
    # Alpha maps to activity density
    alpha = np.zeros_like(A)
    # Smooth alpha feathering near the boundaries
    alpha_mask = A > 0.005
    alpha[alpha_mask] = np.clip(A[alpha_mask] * 400.0, 45, 255)
    alpha = np.clip(alpha, 0, 255).astype(np.int32)
    
    # Combine into ARGB format
    argb = (
        (alpha << 24)
        | (color_r << 16)
        | (color_g << 8)
        | color_b
    )
    
    # Write directly to offscreen image pixels
    img_buffer.load_pixels()
    img_buffer.pixels[:] = argb.flatten()
    img_buffer.update_pixels()

    # 3. Draw HUD and Upscaled Simulation to Main Canvas
    py5.background(8, 4, 16)
    py5.blend_mode(py5.BLEND)
    
    cx, cy = py5.width / 2.0, py5.height / 2.0
    dish_radius = py5.height * 0.44  # Large circular dish
    
    # Draw Lenia grid masked/contained inside the Petri Dish
    py5.image_mode(py5.CENTER)
    # Upscale 256x256 image buffer (bilinear texture filtering handles smoothing automatically)
    py5.image(img_buffer, cx, cy, dish_radius * 2.0, dish_radius * 2.0)
    py5.image_mode(py5.CORNER)
    
    # Draw Petri Dish HUD details
    py5.no_fill()
    
    # Central measurement lines
    py5.stroke(255, 255, 255, 4)
    py5.stroke_weight(0.5)
    py5.line(cx - dish_radius, cy, cx + dish_radius, cy)
    py5.line(cx, cy - dish_radius, cx, cy + dish_radius)
    
    # Concentric rings
    py5.stroke(255, 255, 255, 3)
    py5.circle(cx, cy, dish_radius * 1.0)
    py5.circle(cx, cy, dish_radius * 1.5)
    
    # Primary glass dish boundary
    py5.stroke(255, 255, 255, 14)
    py5.stroke_weight(2.5)
    py5.circle(cx, cy, dish_radius * 2.0)
    
    # Subtle glass reflection arc
    py5.stroke(0, 240, 255, 25)
    py5.stroke_weight(3.0)
    py5.arc(cx, cy, dish_radius * 2.0, dish_radius * 2.0, py5.radians(-55), py5.radians(10))
    
    # Perimeter measurement ticks
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.stroke(255, 255, 255, 12)
    py5.stroke_weight(1.0)
    for angle_deg in range(0, 360, 5):
        py5.rotate(py5.radians(5))
        tick_len = 16.0 if angle_deg % 30 == 0 else 6.0
        py5.line(dish_radius, 0, dish_radius - tick_len, 0)
    py5.pop_matrix()

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame is at frame 450)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
