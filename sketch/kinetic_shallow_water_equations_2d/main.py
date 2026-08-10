from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# --- Simulation Grid Setup ---
GRID_W = 240
GRID_H = 135

# State fields
# h: water height (perturbed thickness)
# u, v: velocities
# b: bottom bathymetry (obstacles / reefs)
h = np.ones((GRID_H, GRID_W), dtype=np.float32) * 2.0
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
v = np.zeros((GRID_H, GRID_W), dtype=np.float32)
b = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Create a beautiful underwater landscape for bathymetry
Y_indices, X_indices = np.indices((GRID_H, GRID_W))

# Large circular reef in center
dist_center = np.sqrt((X_indices - GRID_W / 2) ** 2 + (Y_indices - GRID_H / 2) ** 2)
b += np.exp(-((dist_center) ** 2) / (45.0 ** 2)) * 1.5

# Some smaller submerged peaks
b += np.exp(-(((X_indices - GRID_W * 0.25) ** 2 + (Y_indices - GRID_H * 0.3) ** 2)) / (15.0 ** 2)) * 1.2
b += np.exp(-(((X_indices - GRID_W * 0.75) ** 2 + (Y_indices - GRID_H * 0.7) ** 2)) / (18.0 ** 2)) * 1.0
b += np.exp(-(((X_indices - GRID_W * 0.8) ** 2 + (Y_indices - GRID_H * 0.25) ** 2)) / (12.0 ** 2)) * 0.8

# Cap bathymetry to ensure water doesn't dry out completely in the beginning
b = np.clip(b, 0.0, 1.8)

# Simulation parameters
g = 0.5       # gravity
dt = 0.1      # time step
f = 0.04      # Coriolis coefficient (causes rotation/swirling)
r = 0.005     # bottom friction
nu = 0.06     # artificial viscosity to keep things stable

# Light source (normalized)
Lx, Ly, Lz = 1.0, -1.0, 2.0
L_len = np.sqrt(Lx**2 + Ly**2 + Lz**2)
Lx, Ly, Lz = Lx/L_len, Ly/L_len, Lz/L_len

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def step_simulation(frame):
    global h, u, v
    
    # 3 simulation substeps per frame for faster, smoother wave propagation
    for _ in range(3):
        # Add wave makers: rotating sources and drops
        t_val = frame * 0.05 + _ * 0.016
        
        # Source 1: Top-Left oscillating tide
        h[15:20, 15:20] = 2.0 + 1.2 * np.sin(2.0 * np.pi * t_val * 0.3)
        
        # Source 2: Bottom-Right oscillating tide with a different frequency
        h[-20:-15, -20:-15] = 2.0 + 1.0 * np.sin(2.0 * np.pi * t_val * 0.45 + np.pi/4)
        
        # Source 3: Rotating localized disturbance
        cx = int(GRID_W/2 + GRID_W * 0.35 * np.cos(t_val * 0.15))
        cy = int(GRID_H/2 + GRID_H * 0.35 * np.sin(t_val * 0.15))
        cx = np.clip(cx, 5, GRID_W - 6)
        cy = np.clip(cy, 5, GRID_H - 6)
        h[cy-2:cy+3, cx-2:cx+3] += 0.15 * np.sin(t_val * 0.8)

        # 1. Height update (dh/dt = - div(h * V))
        hu = h * u
        hv = h * v
        # Centered differences
        dhu_dx = (np.roll(hu, -1, axis=1) - np.roll(hu, 1, axis=1)) / 2.0
        dhv_dy = (np.roll(hv, -1, axis=0) - np.roll(hv, 1, axis=0)) / 2.0
        h_new = h - dt * (dhu_dx + dhv_dy)

        # 2. Velocity updates (momentum equations)
        eta = h + b  # free surface level
        deta_dx = (np.roll(eta, -1, axis=1) - np.roll(eta, 1, axis=1)) / 2.0
        deta_dy = (np.roll(eta, -1, axis=0) - np.roll(eta, 1, axis=0)) / 2.0

        u_new = u - dt * (g * deta_dx - f * v + r * u)
        v_new = v - dt * (g * deta_dy + f * u + r * v)

        # Boundary conditions (reflection off walls)
        u_new[:, 0] = 0.0
        u_new[:, -1] = 0.0
        v_new[0, :] = 0.0
        v_new[-1, :] = 0.0

        # Enforce minimum depth to prevent drying artifacts
        dry = h_new < 0.05
        h_new[dry] = 0.05
        u_new[dry] = 0.0
        v_new[dry] = 0.0

        # Artificial viscosity (Laplacian smoothing) for stability
        lap_h = (np.roll(h_new, 1, axis=0) + np.roll(h_new, -1, axis=0) +
                 np.roll(h_new, 1, axis=1) + np.roll(h_new, -1, axis=1) - 4 * h_new)
        lap_u = (np.roll(u_new, 1, axis=0) + np.roll(u_new, -1, axis=0) +
                 np.roll(u_new, 1, axis=1) + np.roll(u_new, -1, axis=1) - 4 * u_new)
        lap_v = (np.roll(v_new, 1, axis=0) + np.roll(v_new, -1, axis=0) +
                 np.roll(v_new, 1, axis=1) + np.roll(v_new, -1, axis=1) - 4 * v_new)

        h = h_new + nu * lap_h
        u = u_new + nu * lap_u
        v = v_new + nu * lap_v

def draw():
    global h, u, v, b
    
    W, H = SIZE
    frame = py5.frame_count
    
    # Step physics
    step_simulation(frame)
    
    # Calculate surface gradient for lighting
    eta = h + b
    deta_dx = (np.roll(eta, -1, axis=1) - np.roll(eta, 1, axis=1)) / 2.0
    deta_dy = (np.roll(eta, -1, axis=0) - np.roll(eta, 1, axis=0)) / 2.0
    
    # Render shading (normal mapping + specular)
    scale = 15.0
    nx = -deta_dx * scale
    ny = -deta_dy * scale
    nz = np.ones_like(nx)
    n_len = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= n_len
    ny /= n_len
    nz /= n_len
    
    # diffuse = dot(N, L)
    dot_NL = nx * Lx + ny * Ly + nz * Lz
    dot_NL_clip = np.clip(dot_NL, 0.0, 1.0)
    
    # reflection vector Rz = 2 * dot_NL * nz - Lz
    rz = 2.0 * dot_NL * nz - Lz
    specular = np.clip(rz, 0.0, 1.0) ** 20.0
    
    # Height mapped to water color (from deep navy to glowing cyan)
    dev = np.clip((h - 2.0) * 1.5 + 0.3, 0.0, 1.0)
    
    # Liquid Colors
    r_base = 5.0 + dev * 30.0
    g_base = 12.0 + dev * 160.0
    b_base = 28.0 + dev * 220.0
    
    # Add diffuse lighting modulation
    r_diff = r_base * (0.4 + 0.6 * dot_NL_clip)
    g_diff = g_base * (0.4 + 0.6 * dot_NL_clip)
    b_diff = b_base * (0.4 + 0.6 * dot_NL_clip)
    
    # Add specular highlights (hot white reflection)
    r_final = np.clip(r_diff + specular * 240.0, 0, 255).astype(np.uint8)
    g_final = np.clip(g_diff + specular * 250.0, 0, 255).astype(np.uint8)
    b_final = np.clip(b_diff + specular * 255.0, 0, 255).astype(np.uint8)
    
    # Upscale to output size
    sx = W // GRID_W
    sy = H // GRID_H
    
    r_up = np.repeat(np.repeat(r_final, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_final, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_final, sy, axis=0), sx, axis=1)[:H, :W]
    
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255  # Alpha
    py5.np_pixels[:, :, 1] = r_up
    py5.np_pixels[:, :, 2] = g_up
    py5.np_pixels[:, :, 3] = b_up
    py5.update_np_pixels()
    
    # Draw vector bathymetry overlay (faint contours to show islands)
    py5.stroke(0, 255, 200, 35)
    py5.no_fill()
    py5.stroke_weight(2)
    
    scale_factor = W / GRID_W
    # Main Island
    py5.ellipse(GRID_W/2 * scale_factor, GRID_H/2 * scale_factor, 90.0 * scale_factor, 90.0 * scale_factor)
    py5.ellipse(GRID_W/2 * scale_factor, GRID_H/2 * scale_factor, 60.0 * scale_factor, 60.0 * scale_factor)
    # Secondary peaks
    py5.ellipse(GRID_W*0.25 * scale_factor, GRID_H*0.3 * scale_factor, 30.0 * scale_factor, 30.0 * scale_factor)
    py5.ellipse(GRID_W*0.75 * scale_factor, GRID_H*0.7 * scale_factor, 36.0 * scale_factor, 36.0 * scale_factor)
    
    # Vignette
    py5.no_stroke()
    for i in range(12):
        alpha = int(4 + i * 3)
        m = i * 20
        py5.fill(2, 4, 12, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)
        
    # Technical HUD Telemetry
    py5.fill(0, 255, 220, 200)
    py5.text_font(py5.create_font("Courier", 16))
    py5.text(f"SYSTEM: 2D SHALLOW WATER EQUATIONS (SWE)", 50, 60)
    py5.text(f"RESOLUTION: 3840 x 2160 (4K)", 50, 85)
    py5.text(f"PHYSICS GRID: {GRID_W} x {GRID_H} (2.5D C-GRID COUPLING)", 50, 110)
    py5.text(f"GRAVITY: {g:.3f} | CORIOLIS SPIN: {f:.3f} | VISCOSITY: {nu:.3f}", 50, 135)
    py5.text(f"FRAME: {frame}/{TOTAL_FRAMES} | DURATION: {DURATION_SEC}s", 50, 160)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (mid-frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
