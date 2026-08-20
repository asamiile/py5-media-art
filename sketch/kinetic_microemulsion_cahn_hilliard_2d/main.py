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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid Size
GRID_W = 320
GRID_H = 180

# Cahn-Hilliard Parameters
kappa = 0.5
dt = 0.02

# State grid
phi = np.random.uniform(-0.1, 0.1, (GRID_H, GRID_W))

# Flow field variables for dynamic advection
flow_x = np.zeros((GRID_H, GRID_W))
flow_y = np.zeros((GRID_H, GRID_W))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def laplacian(f):
    # Periodic boundary laplacian using rolls
    return (
        np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
        np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 4.0 * f
    )

def advect(f, vx, vy):
    # Semi-Lagrangian advection to make the pattern flow smoothly
    # Create coordinate grid
    y, x = np.indices(f.shape)
    
    # Backtrace coordinates
    src_y = (y - vy * 1.2) % GRID_H
    src_x = (x - vx * 1.2) % GRID_W
    
    # Bilinear interpolation indices
    y0 = src_y.astype(int)
    y1 = (y0 + 1) % GRID_H
    x0 = src_x.astype(int)
    x1 = (x0 + 1) % GRID_W
    
    # Bilinear weights
    dx_frac = src_x - x0
    dy_frac = src_y - y0
    
    wa = (1.0 - dx_frac) * (1.0 - dy_frac)
    wb = dx_frac * (1.0 - dy_frac)
    wc = (1.0 - dx_frac) * dy_frac
    wd = dx_frac * dy_frac
    
    return wa * f[y0, x0] + wb * f[y0, x1] + wc * f[y1, x0] + wd * f[y1, x1]

def update_simulation():
    global phi, flow_x, flow_y
    
    # Create a divergence-free flow field using a time-varying stream function
    t = py5.frame_count * 0.015
    y, x = np.indices((GRID_H, GRID_W))
    
    psi_coeff = 12.0
    flow_x = psi_coeff * 0.05 * np.sin(x * 0.05 + t) * np.cos(y * 0.05 - t * 0.7)
    flow_y = -psi_coeff * 0.05 * np.cos(x * 0.05 + t) * np.sin(y * 0.05 - t * 0.7)
    
    # Step 1: Advect the phase field
    phi = advect(phi, flow_x, flow_y)
    
    # Step 2: Cahn-Hilliard step (A=1.0, B=4.0 for strong growth overcoming numerical diffusion)
    mu = phi**3 - 4.0 * phi - kappa * laplacian(phi)
    phi += dt * laplacian(mu)
    
    # Add a small amount of fluctuations/thermal noise
    noise = np.random.normal(0, 0.002, phi.shape)
    phi += noise
    
    # Clamp field slightly to prevent numerical blowup
    phi = np.clip(phi, -2.5, 2.5)

def draw():
    global phi
    
    # Run multiple simulation steps per frame
    for _ in range(4):
        update_simulation()
        
    # Map phi field to colors
    # We want a bioluminescent fluid look
    # Background: Dark Obsidian Abyss
    # Membranes: Purple/Amethyst, Coral/Orange accents
    
    h_screen, w_screen = SIZE[1], SIZE[0]
    
    # Get normals from phi field for specular Phong shading (creates a liquid surface look)
    dy, dx = np.gradient(phi)
    
    # Normalize normals in 3D
    normal_x = -dx
    normal_y = -dy
    normal_z = np.ones_like(phi) * 0.15
    norm = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    normal_x /= norm
    normal_y /= norm
    normal_z /= norm
    
    # Light direction
    lx, ly, lz = 0.5, 0.5, 0.7
    l_norm = np.sqrt(lx**2 + ly**2 + lz**2)
    lx, ly, lz = lx/l_norm, ly/l_norm, lz/l_norm
    
    # Diffuse lighting (dot product)
    diffuse = np.clip(normal_x * lx + normal_y * ly + normal_z * lz, 0.0, 1.0)
    
    # Specular lighting (half-vector)
    hx, hy, hz = lx, ly, lz + 1.0  # View direction is (0, 0, 1)
    h_norm = np.sqrt(hx**2 + hy**2 + hz**2)
    hx, hy, hz = hx/h_norm, hy/h_norm, hz/h_norm
    specular = np.clip(normal_x * hx + normal_y * hy + normal_z * hz, 0.0, 1.0) ** 16
    
    # Create RGB buffer
    rgb_buf = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
    
    # Highlight membranes (where phi is positive)
    scaled_phi = phi / 1.8
    membrane_mask = scaled_phi > 0.0
    val_p = np.clip(scaled_phi, 0.0, 1.0)
    val_n = np.clip(-scaled_phi, 0.0, 1.0)
    
    # Map phase values to color layers
    # Amethyst Purple (Dominant 60%)
    r_amethyst = (val_p * 130 + diffuse * 30).astype(np.uint8)
    g_amethyst = (val_p * 40).astype(np.uint8)
    b_amethyst = (val_p * 230 + specular * 50).astype(np.uint8)
    
    # Coral Orange / Gold (Secondary 30%)
    r_coral = (val_n * 240 + specular * 40).astype(np.uint8)
    g_coral = (val_n * 90 + diffuse * 30).astype(np.uint8)
    b_coral = (val_n * 50).astype(np.uint8)
    
    # Mix layers
    rgb_buf[:, :, 0] = np.where(membrane_mask, r_amethyst, r_coral)
    rgb_buf[:, :, 1] = np.where(membrane_mask, g_amethyst, g_coral)
    rgb_buf[:, :, 2] = np.where(membrane_mask, b_amethyst, b_coral)
    
    # Add a glowing boundary overlay (interface detection)
    interface = np.abs(scaled_phi) < 0.15
    rgb_buf[interface, 0] = np.clip(rgb_buf[interface, 0] + 50, 0, 255)
    rgb_buf[interface, 1] = np.clip(rgb_buf[interface, 1] + 160, 0, 255)  # Teal/Mint highlight
    rgb_buf[interface, 2] = np.clip(rgb_buf[interface, 2] + 180, 0, 255)
    
    # Convert to py5 Image and draw upscaled
    pimg = py5.create_image(GRID_W, GRID_H, py5.RGB)
    pimg.load_pixels()
    r = rgb_buf[:, :, 0].astype(np.int32)
    g = rgb_buf[:, :, 1].astype(np.int32)
    b = rgb_buf[:, :, 2].astype(np.int32)
    a = np.ones_like(r) * 255
    argb = (a << 24) | (r << 16) | (g << 8) | b
    pimg.pixels[:] = argb.flatten()
    pimg.update_pixels()
    
    # Draw upscaled image with smooth interpolation
    py5.image(pimg, 0, 0, w_screen, h_screen)
    
    # Subtle vignette & glass glow
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, w_screen, h_screen)
    
    # Overlay telemetry HUD
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text("MODEL: ADVECTED CAHN-HILLIARD SYSTEM", 60, 80)
    py5.text(f"SIMULATION SPACE: {GRID_W}x{GRID_H} FINITE DIFFERENCE", 60, 120)
    py5.text("MOBILITY CONSTANT (M): 1.0", 60, 160)
    py5.text(f"INTERFACE PARAMETER (kappa): {kappa:.3f}", 60, 200)
    
    py5.text(f"FRAME: {py5.frame_count}/{TOTAL_FRAMES}", 60, h_screen - 80)
    py5.text("RENDER STATUS: 60FPS STABLE ENCODING", w_screen - 500, h_screen - 80)

    # Save frames to disk
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe check
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
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
