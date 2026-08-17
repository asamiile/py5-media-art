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

# Simulation parameters (Run at a lower resolution for performance, then upscale)
Nx, Ny = 512, 288
Lx, Ly = 25.0, 14.0
dx, dy = 2 * Lx / Nx, 2 * Ly / Ny
x = np.linspace(-Lx, Lx, Nx, endpoint=False)
y = np.linspace(-Ly, Ly, Ny, endpoint=False)
X, Y = np.meshgrid(x, y, indexing='ij')

# Wave numbers
kx = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ky = 2 * np.pi * np.fft.fftfreq(Ny, d=dy)
KX, KY = np.meshgrid(kx, ky, indexing='ij')

# Regularized inverse of KX
KX_inv = np.zeros_like(KX)
mask = KX != 0
KX_inv[mask] = 1.0 / KX[mask]

# KP-II Linear dispersion relation
L = 1j * KX**3 - 3j * KY**2 * KX_inv

# De-aliasing filter (2/3 rule)
kx_max = np.max(np.abs(kx))
ky_max = np.max(np.abs(ky))
filter_mask = (np.abs(KX) < (2.0/3.0) * kx_max) & (np.abs(KY) < (2.0/3.0) * ky_max)

# State variables
u = None
dt = 0.002

def init_solitons():
    global u
    # Generate random parameters to ensure variation
    k1 = random.uniform(0.7, 0.9)
    p1 = random.uniform(0.2, 0.4)
    x1 = random.uniform(-10, -5)

    k2 = random.uniform(0.6, 0.8)
    p2 = random.uniform(-0.4, -0.2)
    x2 = random.uniform(-4, 0)

    k3 = random.uniform(0.8, 1.0)
    p3 = random.uniform(0.0, 0.2)
    x3 = random.uniform(2, 6)

    k4 = random.uniform(0.5, 0.7)
    p4 = random.uniform(-0.3, 0.3)
    x4 = random.uniform(-2, 2)

    # Initial condition: sum of multiple line solitons
    u1 = 2 * k1**2 * (1.0 / np.cosh(k1 * (X + p1 * Y - x1)))**2
    u2 = 2 * k2**2 * (1.0 / np.cosh(k2 * (X + p2 * Y - x2)))**2
    u3 = 2 * k3**2 * (1.0 / np.cosh(k3 * (X + p3 * Y - x3)))**2
    u4 = 2 * k4**2 * (1.0 / np.cosh(k4 * (X + p4 * Y - x4)))**2

    u = u1 + u2 + u3 + u4

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    init_solitons()

def rk2_nonlinear(u_curr):
    # u_t = -6 * u * u_x
    # Fourier: d/dt(u_hat) = -3 * i * KX * fft2(u^2)
    u2_hat = np.fft.fft2(u_curr**2) * filter_mask
    rhs_hat = -3j * KX * u2_hat
    return np.real(np.fft.ifft2(rhs_hat))

def step_simulation():
    global u
    # Split-step scheme: linear step in Fourier space
    u_hat = np.fft.fft2(u)
    u_hat = u_hat * np.exp(L * dt)
    u = np.real(np.fft.ifft2(u_hat))

    # Nonlinear step (Heun's method / RK2)
    k1_val = rk2_nonlinear(u)
    u_pred = u + dt * k1_val
    k2_val = rk2_nonlinear(u_pred)
    u = u + 0.5 * dt * (k1_val + k2_val)

def draw():
    step_simulation()

    # Get render buffer actual dimensions
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    # Calculate gradients for specular/liquid lighting
    grad_y, grad_x = np.gradient(u)
    nx = -grad_x * 5.0
    ny = -grad_y * 5.0
    nz = np.ones_like(nx)
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm

    # Light direction (slightly off-center to create nice highlights)
    lx, ly, lz = 0.4, 0.4, 0.9
    l_norm = np.sqrt(lx**2 + ly**2 + lz**2)
    lx, ly, lz = lx/l_norm, ly/l_norm, lz/l_norm

    # Specular shading (Blinn-Phong)
    vx, vy, vz = 0.0, 0.0, 1.0
    hx_vec, hy_vec, hz_vec = lx + vx, ly + vy, lz + vz
    h_norm = np.sqrt(hx_vec**2 + hy_vec**2 + hz_vec**2)
    hx_vec /= h_norm
    hy_vec /= h_norm
    hz_vec /= h_norm

    specular = np.clip(nx*hx_vec + ny*hy_vec + nz*hz_vec, 0, 1) ** 24

    # Normalize u to [0, 1] for coloring
    u_max = max(np.max(u), 1.0)
    u_norm = np.clip(u / u_max, 0, 1)

    # Define color scheme
    color_bg = np.array([3, 5, 9]) / 255.0
    color_teal = np.array([0, 240, 255]) / 255.0
    color_amber = np.array([255, 176, 0]) / 255.0
    color_lime = np.array([57, 255, 20]) / 255.0

    # Initialize color field
    color_field = np.zeros((Nx, Ny, 3))

    # Vectorized color interpolation
    mask1 = u_norm < 0.35
    mask2 = (u_norm >= 0.35) & (u_norm < 0.75)
    mask3 = u_norm >= 0.75

    # Interpolate
    t1 = u_norm / 0.35
    color_field[mask1] = (1 - t1[mask1, None]) * color_bg + t1[mask1, None] * color_teal

    t2 = (u_norm - 0.35) / 0.40
    color_field[mask2] = (1 - t2[mask2, None]) * color_teal + t2[mask2, None] * color_amber

    t3 = (u_norm - 0.75) / 0.25
    color_field[mask3] = (1 - t3[mask3, None]) * color_amber + t3[mask3, None] * color_lime

    # Add specular highlights
    rgb = color_field + specular[..., None] * 0.4

    # Convert to uint8 and scale to screen size
    rgb_uint8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    
    # Transpose back from (Nx, Ny) to match screen shape (H, W)
    rgb_resized = cv2.resize(rgb_uint8, (w, h), interpolation=cv2.INTER_LINEAR)

    # Set py5.np_pixels (including alpha channel as 255)
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

    # Progress logging
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
