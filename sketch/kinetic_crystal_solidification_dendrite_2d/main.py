from pathlib import Path
import sys
import random
import math
import subprocess
import shutil
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes
from lib.animation import frames_dir

# Directories and parameters
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

FPS = 60
TOTAL_FRAMES = 900  # 15 seconds
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# PDE Physics configuration
GRID = 400
DX = 1.0
DT = 0.02

TAU = 1.0          # Phase-field relaxation time
W0 = 1.0           # Interface thickness
LAMBDA = 3.0       # Coupling strength
D = 2.0            # Thermal diffusivity

ANISO_M = 6        # 6-fold hexagonal symmetry (ice crystal structure)
ANISO_EPS = 0.045  # Anisotropy strength
UNDERCOOL = -0.55  # Initial undercooling temperature field

STEPS_PER_FRAME = 3

# Simulation arrays
phi = np.zeros((GRID, GRID), dtype=np.float32)
u = np.full((GRID, GRID), UNDERCOOL, dtype=np.float32)

# Precomputed scaling grid for 4K rendering (nearest-neighbor mapping)
gy = np.zeros(SIZE[1], dtype=np.int32)
gx = np.zeros(SIZE[0], dtype=np.int32)

def setup():
    global phi, u, gy, gx
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Precompute 4K pixel mapping coordinates
    ph, pw = py5.pixel_height, py5.pixel_width
    gy = (np.arange(ph) * GRID / ph).astype(np.int32).clip(0, GRID - 1)
    gx = (np.arange(pw) * GRID / pw).astype(np.int32).clip(0, GRID - 1)
    
    # Seed a small circular solid nucleus at the center
    cx, cy = GRID // 2, GRID // 2
    r_seed = 15
    yy, xx = np.ogrid[:GRID, :GRID]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r_seed ** 2
    phi[mask] = 1.0
    u[mask] = 0.0

def laplacian(f: np.ndarray) -> np.ndarray:
    # 5-point finite difference Laplacian with periodic boundary conditions
    return (np.roll(f, 1, 0) + np.roll(f, -1, 0) + 
            np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4.0 * f) / (DX * DX)

def grad(f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Central difference gradient
    fx = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / (2.0 * DX)
    fy = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / (2.0 * DX)
    return fx, fy

def anisotropic_div_grad(phi_arr: np.ndarray) -> np.ndarray:
    # Computes ∇·[a(θ)²·∇φ] with a(θ) = 1 + ε·cos(m·θ)
    phix, phiy = grad(phi_arr)
    theta = np.arctan2(phiy, phix)
    a = 1.0 + ANISO_EPS * np.cos(ANISO_M * theta)
    a2 = a * a
    
    # Fluxes
    fx = a2 * phix
    fy = a2 * phiy
    
    # Divergence of flux
    div = ((np.roll(fx, -1, 1) - np.roll(fx, 1, 1)) / (2.0 * DX) + 
           (np.roll(fy, -1, 0) - np.roll(fy, 1, 0)) / (2.0 * DX))
    return div

def step_pde():
    global phi, u
    
    # Tau * ∂φ/∂t = W²·∇·[a(θ)²·∇φ] + φ(1−φ)(φ−0.5-λu)
    div_term = anisotropic_div_grad(phi)
    source_term = phi * (1.0 - phi) * (phi - 0.5 - LAMBDA * u)
    
    dphi_dt = (W0 * W0 / TAU) * div_term + source_term / TAU
    phi_new = np.clip(phi + DT * dphi_dt, 0.0, 1.0)
    
    dphi = phi_new - phi
    
    # ∂u/∂t = D·∇²u + 0.5·∂φ/∂t
    du_dt = D * laplacian(u)
    u_new = u + DT * du_dt + 0.5 * dphi
    
    phi = phi_new
    u = u_new

def draw():
    # Update PDE simulation
    for _ in range(STEPS_PER_FRAME):
        step_pde()
        
    # Pre-render: scale fields to 4K using precomputed index coordinates
    # Using np.ix_ to extract the scaled grids
    phi_s = phi[np.ix_(gy, gx)]
    u_s = u[np.ix_(gy, gx)]
    
    # Calculate gradient magnitude of phi at 4K to determine tip glow
    phix, phiy = grad(phi)
    mag = np.sqrt(phix * phix + phiy * phiy)
    mag_s = mag[np.ix_(gy, gx)]
    mag_n = np.clip(mag_s * 15.0, 0.0, 1.0)
    
    # Color Normalization
    u_norm = np.clip((u_s - UNDERCOOL) / (0.0 - UNDERCOOL), 0.0, 1.0)
    
    # 1. Background Liquid (Cobalt Blue warming to twilight Purple near interface)
    bg_r = (u_norm * 65.0).astype(np.int32)
    bg_g = (u_norm * 25.0).astype(np.int32)
    bg_b = (28.0 + u_norm * 75.0).astype(np.int32)
    
    # 2. Solid Phase (Pearlescent Ice-Blue to white core)
    sol_r = (205.0 + phi_s * 50.0).astype(np.int32)
    sol_g = (225.0 + phi_s * 30.0).astype(np.int32)
    sol_b = np.full(phi_s.shape, 255, dtype=np.int32)
    
    # 3. Active Growth Glow (Glowing Neon Amber Gold)
    # The gold is brighter where undercooling u is lower (closer to initial temperature)
    glow_factor = 1.0 - np.clip(u_norm * 0.8, 0.0, 1.0)
    gl_r = np.full(phi_s.shape, 255, dtype=np.int32)
    gl_g = (165.0 + glow_factor * 60.0).astype(np.int32)
    gl_b = (30.0 + glow_factor * 30.0).astype(np.int32)
    
    # Blend colors using solid fraction phi_s and tip gradient mag_n
    # core solid vs interface glow vs liquid background
    r8 = (sol_r * phi_s + (1.0 - phi_s) * (gl_r * mag_n + bg_r * (1.0 - mag_n))).astype(np.uint8)
    g8 = (sol_g * phi_s + (1.0 - phi_s) * (gl_g * mag_n + bg_g * (1.0 - mag_n))).astype(np.uint8)
    b8 = (sol_b * phi_s + (1.0 - phi_s) * (gl_b * mag_n + bg_b * (1.0 - mag_n))).astype(np.uint8)
    
    # Pack into ARGB pixels
    argb = (
        np.int32(-16777216)
        | (r8.astype(np.int32) << 16)
        | (g8.astype(np.int32) << 8)
        | b8.astype(np.int32)
    )
    
    # Write directly to screen pixels
    py5.load_pixels()
    py5.pixels[:] = argb.flatten()
    py5.update_pixels()
    
    # Fail-safe: check standard deviation to prevent blank frames
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress indicator
    if py5.frame_count % 60 == 0:
        solid_frac = float(phi.mean())
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Solid Fraction: {solid_frac:.4f}")
        
    # Compile video on last frame
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot at mid-point
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Cleanup temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
