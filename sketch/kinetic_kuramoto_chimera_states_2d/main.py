from pathlib import Path
import shutil
import subprocess
import sys
import random
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

# Grid configuration
GRID_SCALE = 16
grid_w = SIZE[0] // GRID_SCALE
grid_h = SIZE[1] // GRID_SCALE

# Simulation parameters
alpha_param = 1.46     # Phase lag (critical parameter close to pi/2 for Chimera states)
K = 1.2                # Coupling strength
R_c = 20.0             # Radius of non-local coupling
dt = 0.08              # Integration time step

# Initialize states
# Phase theta: uniform random [0, 2pi]
theta = np.random.uniform(0.0, 2.0 * np.pi, (grid_h, grid_w)).astype(np.float32)
# Internal frequencies (nearly identical to support clean chimera stabilization)
omega = 0.5 + np.random.normal(0.0, 0.01, (grid_h, grid_w)).astype(np.float32)

# Precompute non-local coupling kernel in Fourier space
# The kernel decays exponentially with distance, wrapping around periodically
Y, X = np.ogrid[:grid_h, :grid_w]
dy = np.minimum(Y, grid_h - Y).astype(np.float32)
dx = np.minimum(X, grid_w - X).astype(np.float32)
dist = np.sqrt(dx**2 + dy**2)
G_kernel = np.exp(-dist / R_c, dtype=np.float32)
G_kernel /= np.sum(G_kernel)
G_kernel_fft = np.fft.fft2(G_kernel)

def kuramoto_step():
    """Update Kuramoto coupled oscillator phases using non-local FFT convolution."""
    global theta
    
    # Complex phase parameter
    Z = np.exp(1j * theta)
    
    # Non-local coupling field W via FFT convolution
    W = np.fft.ifft2(np.fft.fft2(Z) * G_kernel_fft)
    
    # Calculate local synchronization order parameter R = |W|
    R = np.abs(W).astype(np.float32)
    
    # Kuramoto interaction: Im( W * exp(-i * (theta + alpha)) )
    interaction = np.imag(W * np.exp(-1j * (theta + alpha_param)))
    
    # Update phases
    theta += dt * (omega + K * interaction)
    theta = np.mod(theta, 2.0 * np.pi)
    
    return R

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Run multiple steps per frame for smooth temporal evolution
    R = None
    for _ in range(5):
        R = kuramoto_step()
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        if np.any(np.isnan(theta)):
            print("[Error] NaN detected in oscillator phases. Aborting.")
            import os
            os._exit(1)
            
    py5.load_np_pixels()
    
    # Upscale matrices to output resolution
    theta_large = np.repeat(np.repeat(theta, GRID_SCALE, axis=0), GRID_SCALE, axis=1)
    R_large = np.repeat(np.repeat(R, GRID_SCALE, axis=0), GRID_SCALE, axis=1)
    
    # Color mapping rules:
    # - Hue is determined by phase theta.
    # - Local order parameter R determines the coherence.
    # - Synchronized domains (high R) have high saturation, solid bright colors, and slow-moving waves.
    # - Desynchronized domains (low R) have low saturation, darker values, and fast sparkling phase changes.
    
    # Color space interpolation (HSL)
    # Target palette:
    # Background / Desynced: Dark Charcoal with faint violet/jade sparkles
    # Synced domains: Glowing violet, jade, and coral pink
    
    # Normalize phase to [0, 1]
    hue = theta_large / (2.0 * np.pi)
    
    # Lightness transitions from dark charcoal (0.05) to glowing structures (0.65)
    # We use a threshold-like curve on R to emphasize borders between order and chaos
    sync_factor = np.clip((R_large - 0.3) / 0.5, 0.0, 1.0) # 0 to 1 mapping
    
    # Interpolate HSL coordinates
    # Hue: Synced areas get full spectrum; desynced areas are shifted towards deep purple/blue (0.75)
    h = 0.75 + (hue - 0.75) * sync_factor
    # Saturation: highly saturated when synced
    s = 0.25 + 0.65 * sync_factor
    # Lightness: glowing synced domains, dim chaotic sea
    l = 0.06 + 0.54 * sync_factor
    
    # HSL to RGB conversion
    c = (1.0 - np.abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - np.abs(np.mod(h * 6.0, 2.0) - 1.0))
    m = l - c / 2.0
    
    i = np.floor(h * 6.0).astype(int) % 6
    
    r_val = np.choose(i, [c, x, np.zeros_like(c), np.zeros_like(c), x, c]) + m
    g_val = np.choose(i, [x, c, c, x, np.zeros_like(c), np.zeros_like(c)]) + m
    b_val = np.choose(i, [np.zeros_like(c), np.zeros_like(c), x, c, c, x]) + m
    
    r = (r_val * 255.0).clip(0, 255).astype(np.uint8)
    g = (g_val * 255.0).clip(0, 255).astype(np.uint8)
    b = (b_val * 255.0).clip(0, 255).astype(np.uint8)
    
    # Write directly to ARGB pixel buffer
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r   # Red
    py5.np_pixels[:, :, 2] = g   # Green
    py5.np_pixels[:, :, 3] = b   # Blue
    
    py5.update_np_pixels()
    
    # Fail-safe checks
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)
            
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
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
