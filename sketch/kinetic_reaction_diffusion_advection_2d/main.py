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

# Simulation grid: downsampled for fast reaction-diffusion updates, then upscaled to 4K
GRID_W = 320
GRID_H = 180

# Gray-Scott Parameters (Bacteria-like spots / divisions)
Du = 0.16
Dv = 0.08
F = 0.035
K = 0.060

u = np.ones((GRID_H, GRID_W), dtype=np.float32)
v = np.zeros((GRID_H, GRID_W), dtype=np.float32)

def setup():
    global u, v
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed random high-concentration spots of chemical V
    for _ in range(15):
        r = np.random.randint(6, 12)
        cx = np.random.randint(r, GRID_W - r)
        cy = np.random.randint(r, GRID_H - r)
        u[cy-r:cy+r, cx-r:cx+r] = 0.50
        v[cy-r:cy+r, cx-r:cx+r] = 0.25
        # Add random perturbations
        noise_shape = (2*r, 2*r)
        u[cy-r:cy+r, cx-r:cx+r] += np.random.uniform(-0.02, 0.02, noise_shape)
        v[cy-r:cy+r, cx-r:cx+r] += np.random.uniform(-0.02, 0.02, noise_shape)

def update_simulation(frame):
    global u, v
    
    # Run multiple micro-steps per frame to speed up pattern propagation
    for _ in range(12):
        # Calculate Laplacian using fast NumPy rolls (periodic boundary conditions)
        lap_u = (
            np.roll(u, 1, axis=0) + np.roll(u, -1, axis=0) +
            np.roll(u, 1, axis=1) + np.roll(u, -1, axis=1) - 4 * u
        )
        lap_v = (
            np.roll(v, 1, axis=0) + np.roll(v, -1, axis=0) +
            np.roll(v, 1, axis=1) + np.roll(v, -1, axis=1) - 4 * v
        )
        
        # Gray-Scott equations
        uvv = u * v * v
        du = Du * lap_u - uvv + F * (1.0 - u)
        dv = Dv * lap_v + uvv - (F + K) * v
        
        u += du
        v += dv
        
        # Dynamic Semi-Lagrangian Advection
        # Generate wind vectors using Perlin noise
        scale_x = 0.005
        scale_y = 0.005
        
        # Grid coordinates
        Y_idx, X_idx = np.indices((GRID_H, GRID_W), dtype=np.float32)
        
        # Calculate wind angle
        wind_angle = py5.noise(frame * 0.004) * py5.TWO_PI * 1.5
        wind_speed = 0.45
        
        # Local noise drift perturbation
        dx_pert = np.array([[py5.noise(x * scale_x, y * scale_y, frame * 0.003) - 0.5 for x in range(GRID_W)] for y in range(GRID_H)], dtype=np.float32) * 0.8
        dy_pert = np.array([[py5.noise(x * scale_x, y * scale_y, frame * 0.003 + 12.3) - 0.5 for x in range(GRID_W)] for y in range(GRID_H)], dtype=np.float32) * 0.8
        
        vx = np.cos(wind_angle) * wind_speed + dx_pert
        vy = np.sin(wind_angle) * wind_speed + dy_pert
        
        # Advect back in time
        src_x = np.clip(X_idx - vx, 0, GRID_W - 1)
        src_y = np.clip(Y_idx - vy, 0, GRID_H - 1)
        
        # Bilinear interpolation for advection
        x0 = np.floor(src_x).astype(np.int32)
        x1 = np.clip(x0 + 1, 0, GRID_W - 1)
        y0 = np.floor(src_y).astype(np.int32)
        y1 = np.clip(y0 + 1, 0, GRID_H - 1)
        
        wx = src_x - x0
        wy = src_y - y0
        
        # Interpolate chemical fields
        u = (
            (1 - wx) * (1 - wy) * u[y0, x0] +
            wx * (1 - wy) * u[y0, x1] +
            (1 - wx) * wy * u[y1, x0] +
            wx * wy * u[y1, x1]
        )
        
        v = (
            (1 - wx) * (1 - wy) * v[y0, x0] +
            wx * (1 - wy) * v[y0, x1] +
            (1 - wx) * wy * v[y1, x0] +
            wx * wy * v[y1, x1]
        )
        
        # Periodic boundaries clipping safety
        u = np.clip(u, 0.0, 1.0)
        v = np.clip(v, 0.0, 1.0)

def draw():
    frame = py5.frame_count
    
    # Step physics simulation
    update_simulation(frame)
    
    # Map high concentrations of V to the color palette
    # Color palette: Solar Amber Gold (#FF9E00), Bioluminescent Emerald Green (#00F5D4), Warm Plum (#7B2CBF)
    # Background: (0, 0, 0)
    
    r_grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
    g_grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
    b_grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
    
    # Calculate concentrations thresholds
    mask_dense = v > 0.4
    mask_mid = (v <= 0.4) & (v > 0.15)
    
    # Dense V -> Solar Amber Gold (#FF9E00) -> (255, 158, 0)
    t_dense = (v[mask_dense] - 0.4) / 0.6
    r_grid[mask_dense] = (158 + (255 - 158) * t_dense).astype(np.uint8)
    g_grid[mask_dense] = (245 + (158 - 245) * t_dense).astype(np.uint8) # Blend from Emerald Green
    b_grid[mask_dense] = (212 + (0 - 212) * t_dense).astype(np.uint8)
    
    # Mid V -> Bioluminescent Emerald Green (#00F5D4) -> (0, 245, 212)
    t_mid = (v[mask_mid] - 0.15) / 0.25
    r_grid[mask_mid] = (123 + (0 - 123) * t_mid).astype(np.uint8) # Blend from Plum
    g_grid[mask_mid] = (44 + (245 - 44) * t_mid).astype(np.uint8)
    b_grid[mask_mid] = (191 + (212 - 191) * t_mid).astype(np.uint8)
    
    # Low V -> Warm Plum/Violet (#7B2CBF) -> (123, 44, 191)
    mask_low = (v <= 0.15) & (v > 0.02)
    t_low = (v[mask_low] - 0.02) / 0.13
    r_grid[mask_low] = (123 * t_low).astype(np.uint8)
    g_grid[mask_low] = (44 * t_low).astype(np.uint8)
    b_grid[mask_low] = (191 * t_low).astype(np.uint8)

    # Upscale back to native 4K size (3840x2160)
    W, H = SIZE
    sx = W // GRID_W
    sy = H // GRID_H
    
    r_up = np.repeat(np.repeat(r_grid, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_grid, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_grid, sy, axis=0), sx, axis=1)[:H, :W]
    
    # Draw frame via np_pixels
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255  # Alpha
    py5.np_pixels[:, :, 1] = r_up
    py5.np_pixels[:, :, 2] = g_up
    py5.np_pixels[:, :, 3] = b_up
    py5.update_np_pixels()
    
    # HUD overlay info
    py5.fill(255, 158, 0, 200)
    py5.text_font(py5.create_font("Courier", 16))
    py5.text("SYSTEM: REACTION DIFFUSION MORPHOGENESIS", 50, 60)
    py5.text("ALGORITHM: GRAY-SCOTT SYSTEM COUPLED WITH SEMI-LAGRANGIAN ADVECTION", 50, 85)
    py5.text(f"FEED: {F:.4f} | KILL: {K:.4f} | GRID: {GRID_W}x{GRID_H} (upscaled)", 50, 110)
    py5.text(f"FRAME: {frame}/{TOTAL_FRAMES} | DURATION: {DURATION_SEC}s", 50, 135)
    
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
