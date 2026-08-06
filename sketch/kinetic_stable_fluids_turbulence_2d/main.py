"""
kinetic_stable_fluids_turbulence_2d
A 4K kinetic visualization of Jos Stam's Stable Fluids algorithm, solving the 2D incompressible
Navier-Stokes equations on a periodic grid to create organic bioluminescent smoke, eddies, and vortices.
"""
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

# --- Simulation Grid Size ---
GRID_W = 240
GRID_H = 135

# Grid coordinate indices for vectorization
Y, X = np.indices((GRID_H, GRID_W))

# --- Stable Fluids State ---
# Velocity fields (u: horizontal, v: vertical)
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
v = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Dye density grids for color channels (R, G, B)
dye_r = np.zeros((GRID_H, GRID_W), dtype=np.float32)
dye_g = np.zeros((GRID_H, GRID_W), dtype=np.float32)
dye_b = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Pressure field
p = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def advect(f, u_vel, v_vel, dt):
    """Semi-Lagrangian advection with toroidal wrapping boundaries."""
    # Find source coordinates
    x_src = X - dt * u_vel
    y_src = Y - dt * v_vel
    
    # Wrap coordinates (periodic boundaries)
    x_src = np.mod(x_src, GRID_W)
    y_src = np.mod(y_src, GRID_H)
    
    # Bilinear interpolation corners
    x0 = np.floor(x_src).astype(np.int32) % GRID_W
    x1 = (x0 + 1) % GRID_W
    y0 = np.floor(y_src).astype(np.int32) % GRID_H
    y1 = (y0 + 1) % GRID_H
    
    # Interpolation weights
    wx = x_src - x0
    wy = y_src - y0
    
    # Interpolate values
    f00 = f[y0, x0]
    f10 = f[y0, x1]
    f01 = f[y1, x0]
    f11 = f[y1, x1]
    
    return ((1.0 - wy) * ((1.0 - wx) * f00 + wx * f10) +
            wy * ((1.0 - wx) * f01 + wx * f11))


def project():
    """Jacobi relaxation to compute pressure and project velocity to divergence-free field."""
    global u, v, p
    p.fill(0)
    
    # Divergence: 0.5 * (u_east - u_west + v_south - v_north)
    div = 0.5 * (
        np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1) +
        np.roll(v, -1, axis=0) - np.roll(v, 1, axis=0)
    )
    
    # Jacobi iteration to solve Poisson equation
    for _ in range(20):
        p = (
            np.roll(p, 1, axis=1) + np.roll(p, -1, axis=1) +
            np.roll(p, 1, axis=0) + np.roll(p, -1, axis=0) - div
        ) / 4.0
        
    # Subtract pressure gradient from velocity field
    u -= 0.5 * (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1))
    v -= 0.5 * (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0))


def add_forces(t):
    """Inject dynamic velocity forces and color dye density in rotating patterns."""
    global u, v, dye_r, dye_g, dye_b
    
    # Create several rotating vortex injects
    num_injects = 4
    for i in range(num_injects):
        angle = 2.0 * np.pi * t / 5.0 + (i * 2.0 * np.pi / num_injects)
        radius = GRID_H * 0.3
        cx = GRID_W / 2.0 + radius * np.cos(angle)
        cy = GRID_H / 2.0 + radius * np.sin(angle * 1.5)
        
        # Distance squared grid
        dist_sq = (X - cx)**2 + (Y - cy)**2
        mask = dist_sq < 8.0**2
        
        # Compute force vector perpendicular to circle radius
        fx = -np.sin(angle) * 1.5
        fy = np.cos(angle) * 1.5
        
        # Inject velocity
        u[mask] += fx
        v[mask] += fy
        
        # Inject colorful dyes without accumulating infinitely
        if i % 3 == 0:
            dye_r[mask] = np.maximum(dye_r[mask], 0.9)
            dye_g[mask] = np.maximum(dye_g[mask], 0.1)
            dye_b[mask] = np.maximum(dye_b[mask], 0.95)
        elif i % 3 == 1:
            dye_r[mask] = np.maximum(dye_r[mask], 0.0)
            dye_g[mask] = np.maximum(dye_g[mask], 0.95)
            dye_b[mask] = np.maximum(dye_b[mask], 0.85)
        else:
            dye_r[mask] = np.maximum(dye_r[mask], 0.95)
            dye_g[mask] = np.maximum(dye_g[mask], 0.85)
            dye_b[mask] = np.maximum(dye_b[mask], 0.0)


def step_simulation(t):
    global u, v, dye_r, dye_g, dye_b
    
    # Add external forces
    add_forces(t)
    
    # Advect velocities (semi-Lagrangian self-advection) with viscosity damping
    dt = 0.8
    u_new = advect(u, u, v, dt)
    v_new = advect(v, u, v, dt)
    
    u = u_new * 0.985
    v = v_new * 0.985
    
    # Project to make velocity divergence-free
    project()
    
    # Advect and diffuse dye channels (decay rate for dissipating wisps)
    dye_r = advect(dye_r, u, v, dt) * 0.975
    dye_g = advect(dye_g, u, v, dt) * 0.975
    dye_b = advect(dye_b, u, v, dt) * 0.975


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    print(f"[Setup] Stable Fluids grid initialized: {GRID_W}x{GRID_H}")


def draw():
    W, H = SIZE
    frame = py5.frame_count
    t = frame / FPS
    
    step_simulation(t)
    
    # Upscale dye fields to output resolution (using repeat expansion)
    sx = W // GRID_W
    sy = H // GRID_H
    
    # Map raw dye concentration into glowing pixel values
    r_grid = np.clip(dye_r * 255.0, 0, 255).astype(np.uint8)
    g_grid = np.clip(dye_g * 255.0, 0, 255).astype(np.uint8)
    b_grid = np.clip(dye_b * 255.0, 0, 255).astype(np.uint8)
    
    r_up = np.repeat(np.repeat(r_grid, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_grid, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_grid, sy, axis=0), sx, axis=1)[:H, :W]
    
    # Write directly to screen buffer
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_up
    py5.np_pixels[:, :, 2] = g_up
    py5.np_pixels[:, :, 3] = b_up
    py5.update_np_pixels()
    
    # Vignette shadow
    for i in range(16):
        alpha = int(3 + i * 4)
        m = i * 22
        py5.fill(8, 8, 16, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)
        
    # Telemetry HUD
    py5.fill(255, 255, 255, 140)
    py5.text_size(20)
    py5.text(f"t={t:.2f}s | velocity_max: {np.hypot(u, v).max():.2f} | grid: {GRID_W}x{GRID_H} | method: Stable Fluids", 50, H - 50)
    
    # Blank screen safety check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)
            
    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")
        
    if frame == TOTAL_FRAMES // 2:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)


py5.run_sketch()
