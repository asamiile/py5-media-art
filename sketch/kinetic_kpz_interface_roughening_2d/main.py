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

# KPZ simulation parameters
SIM_W = 480
SIM_H = 270
nu = 0.5        # Surface tension coefficient (smoothing)
lmbda = 2.0     # Nonlinear growth coefficient
noise_std = 0.15 # Stochastic noise intensity
dt = 0.1

# Initialize height grid
h = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Colors in RGB (normalized to 0-1)
COLOR_BG = np.array([5, 5, 8], dtype=np.float32) / 255.0         # Deep Obsidian
COLOR_LOW = np.array([58, 26, 92], dtype=np.float32) / 255.0      # Amethyst Purple
COLOR_MID = np.array([229, 169, 59], dtype=np.float32) / 255.0    # Amber Gold
COLOR_HIGH = np.array([0, 240, 255], dtype=np.float32) / 255.0    # Phosphor Cyan

# Memory holder for the preview frame to avoid disk reads
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    # Clean and recreate frames directory
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed height field with some initial organic structures
    global h
    x = np.linspace(0, 4 * np.pi, SIM_W)
    y = np.linspace(0, 2 * np.pi, SIM_H)
    X, Y = np.meshgrid(x, y)
    h += 2.0 * np.sin(X) * np.cos(Y)


def draw():
    global h, img_rgb_mid
    
    # 1. Update KPZ Equation (periodic boundaries)
    laplacian = (
        np.roll(h, 1, axis=0) + np.roll(h, -1, axis=0) +
        np.roll(h, 1, axis=1) + np.roll(h, -1, axis=1) - 4 * h
    )
    
    # Gradients
    grad_x = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    grad_y = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    grad_sq = grad_x**2 + grad_y**2
    
    # White noise
    noise = np.random.normal(0, noise_std, size=h.shape).astype(np.float32)
    
    # KPZ PDE step
    dh = nu * laplacian + 0.5 * lmbda * grad_sq + noise
    h += dh * dt
    
    # Normalize height for coloring and contour mapping
    h_min, h_max = h.min(), h.max()
    h_norm = (h - h_min) / (h_max - h_min + 1e-5)
    
    # 2. Compute Normals of the low-res surface for specular shading
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    
    # Normal vector N = (-dx, -dy, 1) normalized
    scale_factor = 10.0
    nx = -dx * scale_factor
    ny = -dy * scale_factor
    nz = np.ones_like(h)
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm
    
    # 3. Light source moving in circle
    angle = py5.frame_count * 0.02
    lx = np.cos(angle)
    ly = np.sin(angle)
    lz = 0.6
    l_norm = np.sqrt(lx**2 + ly**2 + lz**2)
    lx /= l_norm
    ly /= l_norm
    lz /= l_norm
    
    # Diffuse component
    diffuse = nx * lx + ny * ly + nz * lz
    diffuse = np.clip(diffuse, 0.0, 1.0)
    
    # Specular component (Blinn-Phong)
    hx = lx
    hy = ly
    hz = lz + 1.0
    h_norm_v = np.sqrt(hx**2 + hy**2 + hz**2)
    hx /= h_norm_v
    hy /= h_norm_v
    hz /= h_norm_v
    
    specular = nx * hx + ny * hy + nz * hz
    specular = np.clip(specular, 0.0, 1.0) ** 32.0  # Shininess power
    
    # 4. Base Color mapping using height
    mask_low = h_norm < 0.5
    t_low = h_norm / 0.5
    color_base = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    
    # Lerp background/low color to mid color
    color_base[mask_low] = (
        (1.0 - t_low[mask_low])[:, None] * COLOR_LOW +
        t_low[mask_low][:, None] * COLOR_MID
    )
    # Lerp mid color to high/cyan color
    color_base[~mask_low] = (
        (1.0 - (t_low[~mask_low] - 1.0))[:, None] * COLOR_MID +
        (t_low[~mask_low] - 1.0)[:, None] * COLOR_HIGH
    )
    
    # Mix with background color based on overall profile
    weight = np.clip(h_norm * 1.5, 0.0, 1.0)[:, :, None]
    color_base = (1.0 - weight) * COLOR_BG + weight * color_base
    
    # Apply shading: Base color * (Ambient + Diffuse) + Specular * Accent
    ambient = 0.15
    lit_color = color_base * (ambient + diffuse[:, :, None] * 0.85) + specular[:, :, None] * COLOR_HIGH
    
    # 5. Add dynamic glowing contour rings
    contour_freq = 20.0
    contour_width = 0.95
    contours = np.sin(h_norm * contour_freq * np.pi)
    contour_mask = np.abs(contours) > contour_width
    
    # Add neon cyan glow on contours
    glow_factor = (np.abs(contours) - contour_width) / (1.0 - contour_width + 1e-5)
    glow_factor = np.clip(glow_factor, 0.0, 1.0)
    lit_color[contour_mask] += (glow_factor[contour_mask][:, None] * COLOR_HIGH * 0.6)
    
    # 6. Upscale the low-res shaded RGB image to 4K / target output size using bilinear interpolation
    lit_color_full = cv2.resize(lit_color, (SIZE[0], SIZE[1]), interpolation=cv2.INTER_LINEAR)
    
    # Convert to 8-bit RGB
    img_rgb = (np.clip(lit_color_full, 0.0, 1.0) * 255.0).astype(np.uint8)
    
    # Save the middle frame in memory
    if py5.frame_count == TOTAL_FRAMES // 2:
        img_rgb_mid = img_rgb.copy()
        
    # Write directly to py5 np_pixels
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = img_rgb[:, :, 0] # R
    py5.np_pixels[:, :, 1] = img_rgb[:, :, 1] # G
    py5.np_pixels[:, :, 2] = img_rgb[:, :, 2] # B
    py5.np_pixels[:, :, 3] = 255              # A
    py5.update_np_pixels()
    
    # Save frame as JPEG (highly compressed, much faster writes than PNG)
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Progress and blank screen check
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
        
        # Save a preview snapshot directly from memory as PNG
        if img_rgb_mid is not None:
            # cv2 expects BGR
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
