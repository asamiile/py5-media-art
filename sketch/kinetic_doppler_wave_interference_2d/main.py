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

# FDTD Wave simulation parameters
SIM_W = 480
SIM_H = 270
c_sq = 0.25     # Wave speed term (stable under Courant limit < 0.5)
damping = 0.015  # Viscous decay
source_amp = 8.0 # Source displacement amplitude

# Initialize wave grids
u = np.zeros((SIM_H, SIM_W), dtype=np.float32)
u_prev = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Colors in RGB (normalized to 0-1)
COLOR_BG = np.array([4, 3, 13], dtype=np.float32) / 255.0         # Indigo Void
COLOR_TROUGH = np.array([17, 37, 94], dtype=np.float32) / 255.0    # Deep Cobalt Blue
COLOR_MID = np.array([46, 196, 182], dtype=np.float32) / 255.0     # Phosphor Mint Green
COLOR_CREST = np.array([255, 159, 28], dtype=np.float32) / 255.0   # Solar Amber Gold

# Memory holder for the preview frame
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    # Clean and recreate frames directory
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)


def inject_source(grid, x, y, val):
    """Injects a wave source smoothly using a tiny Gaussian footprint."""
    ix = int(x)
    iy = int(y)
    for dy in [-2, -1, 0, 1, 2]:
        for dx in [-2, -1, 0, 1, 2]:
            px = (ix + dx) % SIM_W
            py = (iy + dy) % SIM_H
            dist_sq = (px - x)**2 + (py - y)**2
            weight = np.exp(-dist_sq / 1.2)
            grid[py, px] += val * weight


def draw():
    global u, u_prev, img_rgb_mid
    
    t = py5.frame_count * 0.05
    
    # 1. Inject wave sources along dynamic orbits
    # Source 1: Circle
    s1_x = SIM_W / 2 + 120 * np.cos(t * 0.4)
    s1_y = SIM_H / 2 + 80 * np.sin(t * 0.4)
    val1 = source_amp * np.sin(t * 4.0)
    inject_source(u, s1_x, s1_y, val1)
    
    # Source 2: Lissajous curve
    s2_x = SIM_W / 2 + 150 * np.cos(t * 0.55)
    s2_y = SIM_H / 2 + 90 * np.sin(t * 0.8)
    val2 = source_amp * np.sin(t * 4.8 + 1.5)
    inject_source(u, s2_x, s2_y, val2)
    
    # Source 3: Figure-8
    s3_x = SIM_W / 2 + 100 * np.cos(t * 0.3)
    s3_y = SIM_H / 2 + 70 * np.sin(t * 0.6)
    val3 = source_amp * np.sin(t * 3.5 - 0.7)
    inject_source(u, s3_x, s3_y, val3)
    
    # 2. Update Wave Equation FDTD step
    # Laplacian using 5-point stencil (NumPy rolls for periodic boundaries)
    laplacian = (
        np.roll(u, 1, axis=0) + np.roll(u, -1, axis=0) +
        np.roll(u, 1, axis=1) + np.roll(u, -1, axis=1) - 4 * u
    )
    
    # Verlet-style wave step with damping
    u_next = 2.0 * u - u_prev + c_sq * laplacian - damping * (u - u_prev)
    
    # Cycle buffers
    u_prev = u.copy()
    u = u_next
    
    # Normalize displacement for rendering [-1, 1] range mapping
    scale = 3.0
    u_norm = np.clip(u / scale, -1.0, 1.0)
    
    # 3. Compute Normals for specular highlights
    dx = (np.roll(u_norm, -1, axis=1) - np.roll(u_norm, 1, axis=1)) * 0.5
    dy = (np.roll(u_norm, -1, axis=0) - np.roll(u_norm, 1, axis=0)) * 0.5
    
    # Surface normal vector (low-res)
    normal_strength = 8.0
    nx = -dx * normal_strength
    ny = -dy * normal_strength
    nz = np.ones_like(u_norm)
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm
    
    # 4. Light source orbits above
    angle = py5.frame_count * 0.015
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
    specular = np.clip(specular, 0.0, 1.0) ** 24.0
    
    # 5. Base Color Mapping based on positive (crests) and negative (troughs) displacement
    color_base = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    
    # Map troughs (u_norm < 0) to indigo/blue
    mask_trough = u_norm < 0.0
    t_trough = -u_norm[mask_trough] # positive weight
    color_base[mask_trough] = (
        (1.0 - t_trough)[:, None] * COLOR_BG +
        t_trough[:, None] * COLOR_TROUGH
    )
    
    # Map crests (u_norm >= 0) to mint green and amber gold
    mask_crest = ~mask_trough
    t_crest = u_norm[mask_crest]
    # Split crests range: 0 -> 0.5 (mint green), 0.5 -> 1.0 (gold)
    mask_mid = t_crest < 0.5
    
    color_base_crests = np.zeros((np.sum(mask_crest), 3), dtype=np.float32)
    
    # Lerp background to mint green
    t_mid = t_crest[mask_mid] / 0.5
    color_base_crests[mask_mid] = (
        (1.0 - t_mid)[:, None] * COLOR_BG +
        t_mid[:, None] * COLOR_MID
    )
    
    # Lerp mint green to gold
    t_high = (t_crest[~mask_mid] - 0.5) / 0.5
    color_base_crests[~mask_mid] = (
        (1.0 - t_high)[:, None] * COLOR_MID +
        t_high[:, None] * COLOR_CREST
    )
    
    color_base[mask_crest] = color_base_crests
    
    # 6. Apply shading: Base color * (Ambient + Diffuse) + Specular
    ambient = 0.12
    lit_color = color_base * (ambient + diffuse[:, :, None] * 0.88) + specular[:, :, None] * COLOR_MID * 0.7
    
    # 7. Upscale shaded frame to 4K
    lit_color_full = cv2.resize(lit_color, (SIZE[0], SIZE[1]), interpolation=cv2.INTER_LINEAR)
    
    # Convert to 8-bit RGB
    img_rgb = (np.clip(lit_color_full, 0.0, 1.0) * 255.0).astype(np.uint8)
    
    # Save preview mid-frame
    if py5.frame_count == TOTAL_FRAMES // 2:
        img_rgb_mid = img_rgb.copy()
        
    # Write directly to py5 np_pixels
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = img_rgb[:, :, 0] # R
    py5.np_pixels[:, :, 1] = img_rgb[:, :, 1] # G
    py5.np_pixels[:, :, 2] = img_rgb[:, :, 2] # B
    py5.np_pixels[:, :, 3] = 255              # A
    py5.update_np_pixels()
    
    # Save frame as JPEG
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Progress check and blank screen prevention
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
