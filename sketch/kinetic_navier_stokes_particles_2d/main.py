from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.fft import fft2, ifft2
from scipy.ndimage import map_coordinates

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

# Fluid Grid Size (scaled down for FFT performance)
SCALE = 3
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

NUM_PARTICLES = 1000000
STEPS_PER_FRAME = 2
DT = 0.5

def init_fluid():
    global kx2, ky2, denom, y_grid, x_grid
    
    # Precompute FFT denominators for the Poisson projection
    kx = np.fft.fftfreq(W) * 2 * np.pi
    ky = np.fft.fftfreq(H) * 2 * np.pi
    kx2, ky2 = np.meshgrid(kx, ky)
    
    # Using the standard 5-point discrete Laplacian in Fourier space
    denom = 2.0 * (np.cos(kx2) - 1.0) + 2.0 * (np.cos(ky2) - 1.0)
    denom[0, 0] = 1.0 # Avoid division by zero at DC component
    
    y_grid, x_grid = np.mgrid[0:H, 0:W]

def project(u, v):
    # Compute divergence: div = du/dx + dv/dy
    div = 0.5 * (np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1) + 
                 np.roll(v, -1, axis=0) - np.roll(v, 1, axis=0))
                 
    # Solve Poisson equation: Laplacian(p) = div
    div_fft = fft2(div)
    p_fft = div_fft / denom
    p = np.real(ifft2(p_fft))
    
    # Subtract gradient of pressure from velocity
    u -= 0.5 * (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1))
    v -= 0.5 * (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0))
    return u, v

def advect_grid(field, u, v, dt):
    # Semi-Lagrangian advection
    pos_y = y_grid - v * dt
    pos_x = x_grid - u * dt
    return map_coordinates(field, [pos_y, pos_x], mode='wrap', order=1)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global u, v, p_pos, colormap
    
    init_fluid()
    u = np.zeros((H, W), dtype=np.float32)
    v = np.zeros((H, W), dtype=np.float32)
    
    # Init particles uniformly
    p_pos = np.random.uniform(0, 1, (NUM_PARTICLES, 2)).astype(np.float32)
    p_pos[:, 0] *= W
    p_pos[:, 1] *= H
    
    # Vaporwave Fluid Colormap (Cyan -> Dark Blue -> Purple -> Hot Pink)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        val = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if val < 0.33:
            p = val / 0.33
            colormap[i, 1:] = [int(p * 20), int(255 - p*200), 255] # Cyan to Dark Blue
        elif val < 0.66:
            p = (val - 0.33) / 0.33
            colormap[i, 1:] = [20 + int(p * 180), 55 - int(p * 55), 255] # Dark Blue to Purple
        else:
            p = (val - 0.66) / 0.34
            colormap[i, 1:] = [200 + int(p * 55), int(p * 100), 255 - int(p * 155)] # Purple to Hot Pink

def step_physics(t):
    global u, v, p_pos
    
    # 1. Add forces (moving vortices)
    for i in range(3):
        # Orbiting positions
        fx = W/2 + np.cos(t * 0.5 + i * 2.09) * (W * 0.3)
        fy = H/2 + np.sin(t * 0.7 + i * 2.09) * (H * 0.3)
        
        # Inject velocity (stirring the fluid)
        dx = x_grid - fx
        dy = y_grid - fy
        dist_sq = dx**2 + dy**2 + 1e-5
        
        # Vortex profile (tangential force)
        force = np.exp(-dist_sq / 1000.0) * 2.0
        u += force * -dy
        v += force * dx
    
    # 2. Advect the velocity field itself
    u_new = advect_grid(u, u, v, DT)
    v_new = advect_grid(v, u, v, DT)
    u, v = u_new, v_new
    
    # 3. Project to divergence-free
    u, v = project(u, v)
    
    # 4. Advect particles
    # Interpolate fluid velocity at particle positions
    p_y, p_x = p_pos[:, 1], p_pos[:, 0]
    p_u = map_coordinates(u, [p_y, p_x], mode='wrap', order=1)
    p_v = map_coordinates(v, [p_y, p_x], mode='wrap', order=1)
    
    p_pos[:, 0] = (p_pos[:, 0] + p_u * DT) % W
    p_pos[:, 1] = (p_pos[:, 1] + p_v * DT) % H

def draw():
    global u, v, p_pos
    
    t = py5.frame_count * 0.05
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Deep space fade (motion blur)
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 240 // 256).astype(np.uint8)
    
    # Calculate Vorticity to color the particles
    # vorticity = dv/dx - du/dy
    dv_dx = 0.5 * (np.roll(v, -1, axis=1) - np.roll(v, 1, axis=1))
    du_dy = 0.5 * (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0))
    vorticity = dv_dx - du_dy
    
    # Interpolate vorticity at particle positions
    p_y, p_x = p_pos[:, 1], p_pos[:, 0]
    p_vort = map_coordinates(vorticity, [p_y, p_x], mode='wrap', order=1)
    
    # Map vorticity (-0.5 to 0.5) to color index (0 to 255)
    # Applying a soft sigmoid or tanh for better contrast
    normalized_vort = np.clip((np.tanh(p_vort * 3.0) + 1.0) / 2.0, 0.0, 1.0)
    color_indices = (normalized_vort * 255).astype(np.uint8)
    
    # Map coordinates to screen size
    sx = (p_pos[:, 0] * SCALE).astype(np.int32)
    sy = (p_pos[:, 1] * SCALE).astype(np.int32)
    
    W_scr, H_scr = SIZE
    valid = (sx >= 0) & (sx < W_scr) & (sy >= 0) & (sy < H_scr)
    
    sx = sx[valid]
    sy = sy[valid]
    c_idx = color_indices[valid]
    
    colors = colormap[c_idx]
    
    flat_indices = sy * W_scr + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    np.add.at(flat_pixels[:, 1], flat_indices, colors[:, 1])
    np.add.at(flat_pixels[:, 2], flat_indices, colors[:, 2])
    np.add.at(flat_pixels[:, 3], flat_indices, colors[:, 3])
    
    # Clamp to 255
    flat_pixels[:, 1:] = np.clip(flat_pixels[:, 1:], 0, 255)
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

py5.run_sketch()
