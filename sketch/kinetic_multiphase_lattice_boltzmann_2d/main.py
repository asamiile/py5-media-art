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

# LBM grid dimensions (Run at lower res for speed, then upscale)
Nx, Ny = 384, 216
G = 2.8 # Coupling constant (repulsion)
tau = 1.0

# D2Q9 velocities and weights
e = np.array([
    [0, 0],
    [1, 0], [0, 1], [-1, 0], [0, -1],
    [1, 1], [-1, 1], [-1, -1], [1, -1]
])
w = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])

# State variables
f_A = None
f_B = None

def get_feq(rho, ux, uy):
    feq = np.zeros((9, Nx, Ny))
    u2 = ux**2 + uy**2
    for i in range(9):
        eu = e[i, 0]*ux + e[i, 1]*uy
        feq[i] = w[i] * rho * (1.0 + 3.0*eu + 4.5*eu**2 - 1.5*u2)
    return feq

def setup():
    global f_A, f_B
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize densities: total density = 1.0
    np.random.seed(random.randint(0, 10000))
    rho_A = 0.5 + np.random.normal(0, 0.05, size=(Nx, Ny))
    rho_B = 1.0 - rho_A
    
    # Add multiple circular droplets to seed the mixture
    X, Y = np.meshgrid(np.arange(Nx), np.arange(Ny), indexing='ij')
    for _ in range(12):
        cx = random.randint(30, Nx-30)
        cy = random.randint(30, Ny-30)
        r = random.randint(12, 24)
        mask = (X - cx)**2 + (Y - cy)**2 < r**2
        rho_A[mask] = 0.98
        rho_B[mask] = 0.02
        
    f_A = get_feq(rho_A, np.zeros((Nx, Ny)), np.zeros((Nx, Ny)))
    f_B = get_feq(rho_B, np.zeros((Nx, Ny)), np.zeros((Nx, Ny)))

def step_simulation():
    global f_A, f_B
    
    # 1. Macroscopic variables
    rho_A = np.sum(f_A, axis=0)
    rho_B = np.sum(f_B, axis=0)
    
    rho_A = np.clip(rho_A, 1e-6, 1.0)
    rho_B = np.clip(rho_B, 1e-6, 1.0)
    
    ux_A = np.sum(f_A * e[:, 0, None, None], axis=0) / rho_A
    uy_A = np.sum(f_A * e[:, 1, None, None], axis=0) / rho_A
    
    ux_B = np.sum(f_B * e[:, 0, None, None], axis=0) / rho_B
    uy_B = np.sum(f_B * e[:, 1, None, None], axis=0) / rho_B
    
    # 2. Interaction Force
    sum_x_A = np.zeros((Nx, Ny))
    sum_y_A = np.zeros((Nx, Ny))
    sum_x_B = np.zeros((Nx, Ny))
    sum_y_B = np.zeros((Nx, Ny))
    
    for i in range(9):
        rho_B_rolled = np.roll(np.roll(rho_B, shift=e[i, 0], axis=0), shift=e[i, 1], axis=1)
        sum_x_A += w[i] * rho_B_rolled * e[i, 0]
        sum_y_A += w[i] * rho_B_rolled * e[i, 1]
        
        rho_A_rolled = np.roll(np.roll(rho_A, shift=e[i, 0], axis=0), shift=e[i, 1], axis=1)
        sum_x_B += w[i] * rho_A_rolled * e[i, 0]
        sum_y_B += w[i] * rho_A_rolled * e[i, 1]
        
    Fx_A = - G * rho_A * sum_x_A
    Fy_A = - G * rho_A * sum_y_A
    Fx_B = - G * rho_B * sum_x_B
    Fy_B = - G * rho_B * sum_y_B
    
    # 3. Common velocity (u_prime)
    u_prime_x = (rho_A * ux_A + rho_B * ux_B) / (rho_A + rho_B)
    u_prime_y = (rho_A * uy_A + rho_B * uy_B) / (rho_A + rho_B)
    
    # 4. Add moving vortex forces to stir the fluids
    # Let's create two rotating vortices orbiting the center
    t = py5.frame_count * 0.02
    cx1, cy1 = Nx/2 + 70 * np.cos(t), Ny/2 + 40 * np.sin(t)
    cx2, cy2 = Nx/2 - 70 * np.cos(t), Ny/2 - 40 * np.sin(t)
    
    X, Y = np.meshgrid(np.arange(Nx), np.arange(Ny), indexing='ij')
    
    # Vortex 1
    dx1, dy1 = X - cx1, Y - cy1
    d2_1 = dx1**2 + dy1**2 + 10.0
    f1_x = -0.15 * dy1 / d2_1 * np.exp(-d2_1 / 60**2)
    f1_y = 0.15 * dx1 / d2_1 * np.exp(-d2_1 / 60**2)
    
    # Vortex 2
    dx2, dy2 = X - cx2, Y - cy2
    d2_2 = dx2**2 + dy2**2 + 10.0
    f2_x = 0.15 * dy2 / d2_2 * np.exp(-d2_2 / 60**2)
    f2_y = -0.15 * dx2 / d2_2 * np.exp(-d2_2 / 60**2)
    
    u_prime_x += f1_x + f2_x
    u_prime_y += f1_y + f2_y
    
    # 5. Equilibrium velocity including force
    u_eq_A_x = u_prime_x + Fx_A / rho_A
    u_eq_A_y = u_prime_y + Fy_A / rho_A
    u_eq_B_x = u_prime_x + Fx_B / rho_B
    u_eq_B_y = u_prime_y + Fy_B / rho_B
    
    # Limit velocity to prevent numerical blowup
    v_max = 0.15
    u_eq_A_x = np.clip(u_eq_A_x, -v_max, v_max)
    u_eq_A_y = np.clip(u_eq_A_y, -v_max, v_max)
    u_eq_B_x = np.clip(u_eq_B_x, -v_max, v_max)
    u_eq_B_y = np.clip(u_eq_B_y, -v_max, v_max)
    
    # 6. Collision
    feq_A = get_feq(rho_A, u_eq_A_x, u_eq_A_y)
    f_A = f_A - (1.0 / tau) * (f_A - feq_A)
    
    feq_B = get_feq(rho_B, u_eq_B_x, u_eq_B_y)
    f_B = f_B - (1.0 / tau) * (f_B - feq_B)
    
    # 7. Streaming
    for i in range(9):
        f_A[i] = np.roll(np.roll(f_A[i], shift=e[i, 0], axis=0), shift=e[i, 1], axis=1)
        f_B[i] = np.roll(np.roll(f_B[i], shift=e[i, 0], axis=0), shift=e[i, 1], axis=1)
        
    return rho_A, rho_B

def draw():
    rho_A, rho_B = step_simulation()

    # Get render buffer dimensions
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    # Heightfield for lighting (difference between phases)
    height = rho_A - rho_B
    
    # Calculate gradients for specular liquid lighting
    grad_y, grad_x = np.gradient(height)
    nx = -grad_x * 8.0
    ny = -grad_y * 8.0
    nz = np.ones_like(nx)
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm

    # Light direction
    lx, ly, lz = 0.3, 0.3, 0.9
    l_norm = np.sqrt(lx**2 + ly**2 + lz**2)
    lx, ly, lz = lx/l_norm, ly/l_norm, lz/l_norm

    # Specular shading (Blinn-Phong)
    vx, vy, vz = 0.0, 0.0, 1.0
    hx_vec, hy_vec, hz_vec = lx + vx, ly + vy, lz + vz
    h_norm = np.sqrt(hx_vec**2 + hy_vec**2 + hz_vec**2)
    hx_vec /= h_norm
    hy_vec /= h_norm
    hz_vec /= h_norm

    specular = np.clip(nx*hx_vec + ny*hy_vec + nz*hz_vec, 0, 1) ** 20

    # Colors
    color_bg = np.array([2, 4, 8]) / 255.0
    color_amethyst = np.array([153, 51, 255]) / 255.0
    color_coral = np.array([255, 79, 0]) / 255.0
    color_turquoise = np.array([0, 252, 230]) / 255.0

    # Interface mask: high where both phases are present (the boundary)
    interface_mask = 4.0 * rho_A * rho_B
    interface_mask = np.clip(interface_mask, 0, 1)

    # Blend colors
    color_field = np.zeros((Nx, Ny, 3))
    
    # Background blending
    total_rho = rho_A + rho_B
    bg_factor = np.clip(1.0 - total_rho, 0, 1)
    
    color_field += bg_factor[..., None] * color_bg
    # Phase A (Amethyst) and Phase B (Coral)
    color_field += (rho_A[..., None] * color_amethyst)
    color_field += (rho_B[..., None] * color_coral)
    
    # Interface highlight (Turquoise)
    color_field = color_field * (1.0 - interface_mask[..., None] * 0.4) + interface_mask[..., None] * color_turquoise * 0.8

    # Add specular highlights
    rgb = color_field + specular[..., None] * 0.5
    
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
