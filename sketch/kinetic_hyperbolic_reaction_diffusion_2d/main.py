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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid size for square Poincaré Disk simulation
W_sim = 480
H_sim = 480
cx, cy = W_sim / 2.0, H_sim / 2.0
R_disk = 230.0

# Gray-Scott Model Constants
Du = 0.16
Dv = 0.08
F_rate = 0.037
K_rate = 0.060

# Grids
U = np.ones((H_sim, W_sim), dtype=np.float32)
V = np.zeros((H_sim, W_sim), dtype=np.float32)

X_grid, Y_grid = np.meshgrid(np.arange(W_sim), np.arange(H_sim))
dist_grid = np.hypot(X_grid - cx, Y_grid - cy)
r_norm = np.clip(dist_grid / R_disk, 0.0, 1.0)
mask_in = r_norm < 1.0

# Precompute Conformal Factor (Poincaré metric Laplace-Beltrami scaling)
# Scale factor goes to 0 at the boundary, freezing the patterns
conformal = np.zeros((H_sim, W_sim), dtype=np.float32)
# Clip to avoid division by zero or extreme instabilities very close to boundary
r_clipped = np.clip(r_norm, 0.0, 0.98)
conformal[mask_in] = ((1.0 - r_clipped[mask_in] ** 2) ** 2) / 4.0

# Render colors array
colored = np.zeros((H_sim, W_sim, 4), dtype=np.uint8)
colored[..., 3] = 255

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed species V at multiple random coordinates inside the disk
    for _ in range(12):
        theta = random.uniform(0, 2 * np.pi)
        r_seed = random.uniform(0.08, 0.45) * R_disk
        sx = int(cx + r_seed * np.cos(theta))
        sy = int(cy + r_seed * np.sin(theta))
        V[sy - 4:sy + 4, sx - 4:sx + 4] = 1.0

def draw():
    global U, V
    
    # Numerical sub-stepping (2 steps per frame for stability and speed)
    for _ in range(2):
        # 5-point Euclidean Laplacian
        lap_u = np.zeros_like(U)
        lap_u[1:-1, 1:-1] = U[:-2, 1:-1] + U[2:, 1:-1] + U[1:-1, :-2] + U[1:-1, 2:] - 4 * U[1:-1, 1:-1]
        
        lap_v = np.zeros_like(V)
        lap_v[1:-1, 1:-1] = V[:-2, 1:-1] + V[2:, 1:-1] + V[1:-1, :-2] + V[1:-1, 2:] - 4 * V[1:-1, 1:-1]
        
        # Scale to Laplace-Beltrami by multiplying with precomputed conformal factor
        lap_lb_u = conformal * lap_u
        lap_lb_v = conformal * lap_v
        
        # Gray-Scott update formulas
        uv2 = U * V * V
        U += Du * lap_lb_u - uv2 + F_rate * (1.0 - U)
        V += Dv * lap_lb_v + uv2 - (F_rate + K_rate) * V
        
        # Hard Dirichlet boundary conditions at Poincaré horizon
        U[~mask_in] = 1.0
        V[~mask_in] = 0.0

    # --- Render to ARGB ---
    r_val = np.zeros_like(V)
    g_val = np.zeros_like(V)
    b_val = np.zeros_like(V)
    
    # Base dark void color (gets darker near edge)
    r_val[mask_in] = 10.0 + (1.0 - r_norm[mask_in]**2) * 15.0
    g_val[mask_in] = 2.0
    b_val[mask_in] = 18.0 + (1.0 - r_norm[mask_in]**2) * 25.0
    
    # Map species V density to glow palette
    v_val = np.clip(V * 2.6, 0.0, 1.0)
    
    # Dynamic blend between Space Void, Magenta (255, 0, 127) and Mint Green (0, 255, 187)
    r_out = (1.0 - v_val) * r_val + v_val * 255.0 * (1.0 - v_val**2)
    g_out = (1.0 - v_val) * g_val + v_val * 255.0 * (v_val**3)
    b_out = (1.0 - v_val) * b_val + v_val * (127.0 * (1.0 - v_val) + 187.0 * v_val)
    
    colored[mask_in, 0] = np.clip(r_out[mask_in], 0, 255).astype(np.uint8)
    colored[mask_in, 1] = np.clip(g_out[mask_in], 0, 255).astype(np.uint8)
    colored[mask_in, 2] = np.clip(b_out[mask_in], 0, 255).astype(np.uint8)
    colored[mask_in, 3] = 255
    
    # Clean void boundary outside the unit disk
    colored[~mask_in] = [0, 0, 0, 255]
    
    py5.background(0)
    
    # Draw scaled Poincaré disk grid to the center of 16:9 canvas
    img = py5.create_image(W_sim, H_sim, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:] = colored
    img.update_np_pixels()
    
    # Calculate centering parameters
    screen_h = py5.height
    screen_w = py5.width
    scale = screen_h
    offset_x = (screen_w - screen_h) / 2
    py5.image(img, offset_x, 0, scale, scale)
    
    # --- Draw Outer Boundary Ring in 4K ---
    py5.no_fill()
    py5.stroke(0, 255, 187, 80)
    py5.stroke_weight(4)
    # Circle matches exact boundary of R_disk inside the center-scaled view
    disk_scale = scale / W_sim
    center_x = offset_x + cx * disk_scale
    center_y = cy * disk_scale
    radius_4k = R_disk * 2.0 * disk_scale
    
    py5.ellipse(center_x, center_y, radius_4k, radius_4k)
    
    py5.stroke(0, 255, 187, 30)
    py5.stroke_weight(12)
    py5.ellipse(center_x, center_y, radius_4k, radius_4k)
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
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
        
        # Save preview snapshot (middle frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
