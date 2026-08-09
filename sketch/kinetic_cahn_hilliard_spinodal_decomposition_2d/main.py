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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Cahn-Hilliard parameters
SIM_W = 480
SIM_H = 270
D = 0.8          # Diffusion rate
gamma = 0.6      # Surface tension / interface energy
dt = 0.04        # Time step

# Phase field concentration (-1 to 1)
phi = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Colors in RGB (normalized to 0-1)
COLOR_BG = np.array([6, 5, 12], dtype=np.float32) / 255.0         # Deep Purple Void
COLOR_PHASE_A = np.array([12, 100, 180], dtype=np.float32) / 255.0 # Glacial Cobalt Blue
COLOR_PHASE_B = np.array([230, 80, 50], dtype=np.float32) / 255.0  # Coral Orange/Red
COLOR_GLOW = np.array([255, 210, 40], dtype=np.float32) / 255.0   # Golden Glow

# Memory holder for preview
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize with random fluctuations representing a homogeneous state
    global phi
    phi = np.random.uniform(-0.15, 0.15, size=(SIM_H, SIM_W)).astype(np.float32)


def draw():
    global phi, img_rgb_mid
    
    # 1. Update Cahn-Hilliard equations (5-point stencil Laplacians with rolling)
    laplacian_phi = (
        np.roll(phi, 1, axis=0) + np.roll(phi, -1, axis=0) +
        np.roll(phi, 1, axis=1) + np.roll(phi, -1, axis=1) - 4.0 * phi
    )
    
    # Chemical potential mu = phi^3 - phi - gamma * laplacian(phi)
    mu = phi**3 - phi - gamma * laplacian_phi
    
    laplacian_mu = (
        np.roll(mu, 1, axis=0) + np.roll(mu, -1, axis=0) +
        np.roll(mu, 1, axis=1) + np.roll(mu, -1, axis=1) - 4.0 * mu
    )
    
    # Update concentration field
    phi += D * laplacian_mu * dt
    
    # Stabilize boundary values
    phi = np.clip(phi, -1.0, 1.0)
    
    # 2. Compute gradients for boundary detection and normal-mapping
    dx = (np.roll(phi, -1, axis=1) - np.roll(phi, 1, axis=1)) * 0.5
    dy = (np.roll(phi, -1, axis=0) - np.roll(phi, 1, axis=0)) * 0.5
    
    # Interface boundaries have maximum gradients
    grad_mag = np.sqrt(dx**2 + dy**2)
    grad_mag_norm = np.clip(grad_mag * 5.0, 0.0, 1.0)
    
    # 3. Compute Normals of the phase field surface
    scale_factor = 6.0
    nx = -dx * scale_factor
    ny = -dy * scale_factor
    nz = np.ones_like(phi)
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm
    
    # 4. Light source moving in loop
    angle = py5.frame_count * 0.025
    lx = np.cos(angle)
    ly = np.sin(angle)
    lz = 0.5
    l_norm = np.sqrt(lx**2 + ly**2 + lz**2)
    lx /= l_norm
    ly /= l_norm
    lz /= l_norm
    
    # Diffuse & Specular (Blinn-Phong)
    diffuse = nx * lx + ny * ly + nz * lz
    diffuse = np.clip(diffuse, 0.0, 1.0)
    
    hx = lx
    hy = ly
    hz = lz + 1.0
    h_norm_v = np.sqrt(hx**2 + hy**2 + hz**2)
    hx /= h_norm_v
    hy /= h_norm_v
    hz /= h_norm_v
    
    specular = nx * hx + ny * hy + nz * hz
    specular = np.clip(specular, 0.0, 1.0) ** 32.0
    
    # 5. Base Color Mapping based on phase (phi: -1 is Phase A, 1 is Phase B)
    color_base = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    
    # Normalize phi to [0, 1] range for interpolation
    phi_norm = (phi + 1.0) * 0.5
    
    # Map Phase A (low concentration) to Glacial Blue, Phase B (high) to Coral Orange
    # Intermediate values are desaturated/background blend
    mask_low = phi_norm < 0.5
    t_low = phi_norm[mask_low] / 0.5
    color_base[mask_low] = (
        (1.0 - t_low)[:, None] * COLOR_PHASE_A +
        t_low[:, None] * COLOR_BG
    )
    
    mask_high = ~mask_low
    t_high = (phi_norm[mask_high] - 0.5) / 0.5
    color_base[mask_high] = (
        (1.0 - t_high)[:, None] * COLOR_BG +
        t_high[:, None] * COLOR_PHASE_B
    )
    
    # 6. Apply shading
    ambient = 0.15
    lit_color = color_base * (ambient + diffuse[:, :, None] * 0.85) + specular[:, :, None] * 0.5
    
    # 7. Add interface glowing borders
    lit_color += grad_mag_norm[:, :, None] * COLOR_GLOW * 0.65
    
    # 8. Upscale to 4K
    lit_color_full = cv2.resize(lit_color, (SIZE[0], SIZE[1]), interpolation=cv2.INTER_LINEAR)
    
    # Convert to 8-bit RGB
    img_rgb = (np.clip(lit_color_full, 0.0, 1.0) * 255.0).astype(np.uint8)
    
    if py5.frame_count == TOTAL_FRAMES // 2:
        img_rgb_mid = img_rgb.copy()
        
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = img_rgb[:, :, 0] # R
    py5.np_pixels[:, :, 1] = img_rgb[:, :, 1] # G
    py5.np_pixels[:, :, 2] = img_rgb[:, :, 2] # B
    py5.np_pixels[:, :, 3] = 255              # A
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Progress and stability check
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
        
        # Save preview snapshot
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
