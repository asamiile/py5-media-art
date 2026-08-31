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

# Grid configuration: 240x135 grid upscaled by 16x matches 3840x2160 output size
GRID_SCALE = 16
grid_w = SIZE[0] // GRID_SCALE
grid_h = SIZE[1] // GRID_SCALE

# LLG Simulation Parameters
# Normalized parameters that yield stable, beautiful skyrmion textures
J = 1.0       # Ferromagnetic exchange coupling
D = 0.35      # Dzyaloshinskii-Moriya Interaction (DMI) strength
B = 0.04      # External magnetic field along +z
alpha = 0.1   # Gilbert damping
beta = 0.05   # Non-adiabatic spin torque parameter
u = 0.15      # Spin drift velocity (driving current along +x)
dt = 0.1      # Simulation time step

# Spin array: shape (3, grid_h, grid_w) representing Sx, Sy, Sz
S = np.zeros((3, grid_h, grid_w), dtype=np.float32)
# Initialize background ferromagnetic state pointing along +z
S[2, :, :] = 1.0

def create_skyrmion(cx, cy, R=10.0, helicity=np.pi/2):
    """Inject a skyrmion core of radius R at (cx, cy)."""
    global S
    Y, X = np.ogrid[:grid_h, :grid_w]
    dy = (Y - cy).astype(np.float32)
    dx = (X - cx).astype(np.float32)
    r = np.sqrt(dx**2 + dy**2)
    
    # Mask of the skyrmion radius
    mask = r < R
    
    # Angular winding
    theta = np.pi * (1.0 - r / R)
    phi = np.arctan2(dy, dx) + helicity
    
    # Set spin values within the mask
    S[0, :, :] = np.where(mask, np.sin(theta) * np.cos(phi), S[0, :, :])
    S[1, :, :] = np.where(mask, np.sin(theta) * np.sin(phi), S[1, :, :])
    S[2, :, :] = np.where(mask, np.cos(theta), S[2, :, :])
    
    # Re-normalize just in case
    norm = np.linalg.norm(S, axis=0, keepdims=True)
    S /= norm

# Seed initial skyrmions randomly
random.seed(42)
np.random.seed(42)
num_skyrmions = 15
for _ in range(num_skyrmions):
    cx = random.uniform(10, grid_w - 10)
    cy = random.uniform(10, grid_h - 10)
    R = random.uniform(8.0, 14.0)
    create_skyrmion(cx, cy, R=R, helicity=np.pi/2)

def cross(a, b):
    """Vectorized cross product of two shape (3, H, W) spin field arrays."""
    return np.array([
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    ], dtype=np.float32)

def llg_step():
    """Perform one step of LLG integration with Spin Transfer Torque."""
    global S
    
    # 1. Compute shifted neighbors for spatial derivatives
    S_left = np.roll(S, 1, axis=2)
    S_right = np.roll(S, -1, axis=2)
    S_up = np.roll(S, 1, axis=1)
    S_down = np.roll(S, -1, axis=1)
    
    # 2. Exchange field
    H_ex = J * (S_left + S_right + S_up + S_down)
    
    # 3. Interfacial Dzyaloshinskii-Moriya Interaction (DMI) field
    # H_dmi_x = D * (S_left_z - S_right_z)
    # H_dmi_y = D * (S_down_z - S_up_z)
    # H_dmi_z = D * (S_right_x - S_left_x + S_up_y - S_down_y)
    H_dmi = np.zeros_like(S)
    H_dmi[0] = D * (S_left[2] - S_right[2])
    H_dmi[1] = D * (S_down[2] - S_up[2])
    H_dmi[2] = D * (S_right[0] - S_left[0] + S_up[1] - S_down[1])
    
    # 4. Zeeman field (external field along +z)
    H_zeeman = np.zeros_like(S)
    H_zeeman[2] = B
    
    # Total effective field
    H_eff = H_ex + H_dmi + H_zeeman
    
    # 5. Spin Transfer Torque (STT) term due to electric current
    # dS/dx central difference
    dS_dx = 0.5 * (S_right - S_left)
    j_torque = -u * dS_dx
    T_stt = j_torque + beta * cross(S, j_torque)
    
    # 6. LLG Dynamics
    S_cross_H = cross(S, H_eff)
    S_cross_S_cross_H = cross(S, S_cross_H)
    dS_dt = -(S_cross_H + alpha * S_cross_S_cross_H) / (1.0 + alpha**2)
    
    # Combine field and torque updates
    S += dt * (dS_dt + T_stt)
    
    # Normalize to preserve unit vector constraint
    S /= np.linalg.norm(S, axis=0, keepdims=True)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Run multiple micro-steps per frame to ensure stability and smooth motion
    for _ in range(4):
        llg_step()
    
    # Fail-safe check: check for nan or blank screen
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        if np.any(np.isnan(S)):
            print("[Error] NaN detected in spin arrays. Aborting.")
            import os
            os._exit(1)
            
    py5.load_np_pixels()
    
    # Upscale the grid to output resolution using fast repeat
    # Sx, Sy, Sz shape: (grid_h, grid_w)
    Sx_large = np.repeat(np.repeat(S[0], GRID_SCALE, axis=0), GRID_SCALE, axis=1)
    Sy_large = np.repeat(np.repeat(S[1], GRID_SCALE, axis=0), GRID_SCALE, axis=1)
    Sz_large = np.repeat(np.repeat(S[2], GRID_SCALE, axis=0), GRID_SCALE, axis=1)
    
    # Fast HSL/HSV style mapping
    # Hue represents the angle of the spin in the xy-plane
    angle = np.arctan2(Sy_large, Sx_large)
    hue = (angle + np.pi) / (2.0 * np.pi) # normalized [0, 1]
    
    # Brightness / value: Skyrmion cores (Sz close to -1) are highlighted.
    # Background (Sz = 1) is a deep cobalt blue.
    # Out-of-plane deviation (1 - Sz) determines color intensity.
    intensity = 0.5 * (1.0 - Sz_large) # [0, 1] where 1 is core, 0 is background
    
    # We want a base cobalt/navy background when intensity is 0
    # Cobalt base color: Hue 0.65, Saturation 0.8, Lightness 0.15
    # Skyrmion cores: Hue varies, Saturation 0.9, Lightness 0.5 to 0.8
    # We will interpolate HSL values based on intensity
    
    h = 0.65 + (hue - 0.65) * intensity
    s = 0.8 + (0.15 * intensity) # saturate slightly more at cores
    
    # Lightness transitions from deep cobalt (0.08) to glowing cores (up to 0.75)
    l = 0.08 + 0.67 * intensity
    
    # Convert HSL to RGB vectorized
    # HSL to RGB conversion helper
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
    
    # Write to py5 pixels (ARGB format)
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r   # Red
    py5.np_pixels[:, :, 2] = g   # Green
    py5.np_pixels[:, :, 3] = b   # Blue
    
    py5.update_np_pixels()
    
    # Progress and blank screen check
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
