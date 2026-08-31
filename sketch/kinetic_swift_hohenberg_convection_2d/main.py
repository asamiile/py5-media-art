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

# Grid size for pattern simulation
W_sim = 640
H_sim = 360

# Swift-Hohenberg constants
epsilon = 0.25      # Bifurcation parameter
qc = 0.5           # Critical wavenumber
qc2 = qc * qc
qc4 = qc2 * qc2
dt = 0.01           # Stable timestep under CFL condition

# Initialize grid with random small fluctuations
u = (np.random.rand(H_sim, W_sim).astype(np.float32) - 0.5) * 0.1

# Color buffer
colored = np.zeros((H_sim, W_sim, 4), dtype=np.uint8)
colored[..., 3] = 255

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def laplacian(A):
    # Periodic boundary discrete Laplacian
    return (
        np.roll(A, 1, axis=0) + np.roll(A, -1, axis=0) +
        np.roll(A, 1, axis=1) + np.roll(A, -1, axis=1) - 4.0 * A
    )

def draw():
    global u
    
    # Sub-stepping (24 steps per frame for smooth motion and stability)
    for _ in range(24):
        # 1. Compute bi-Laplacian: (L + qc^2)^2 u = L^2 u + 2 qc^2 L u + qc^4 u
        lap = laplacian(u)
        lap_lap = laplacian(lap)
        bi_lap = lap_lap + 2.0 * qc2 * lap + qc4 * u
        
        # 2. Compute dynamic divergence-free velocity field (moving shear rolls)
        t_phase = py5.frame_count * 0.002
        y, x = np.meshgrid(np.arange(W_sim), np.arange(H_sim))
        
        # Stream function psi
        psi = 4.0 * np.sin(x * 0.02 + t_phase) * np.cos(y * 0.025 - 1.2 * t_phase) + \
              2.0 * np.sin(y * 0.045 + 2.0 * t_phase) * np.cos(x * 0.035 + t_phase)
              
        # Velocities derived from stream function: vx = d_psi/dy (axis 1), vy = -d_psi/dx (axis 0)
        vx = np.gradient(psi, axis=1)
        vy = -np.gradient(psi, axis=0)
        
        # 3. Advection term: (v . grad) u
        du_dx = np.gradient(u, axis=1)
        du_dy = np.gradient(u, axis=0)
        advection = vx * du_dx + vy * du_dy
        
        # 4. Update Swift-Hohenberg equations
        u = u + dt * (epsilon * u - bi_lap - u**3 - 0.25 * advection)

    # --- Render ---
    u_norm = np.clip(u * 1.5, -1.0, 1.0)
    
    # Glow logic: Ember oranges (positive) and deep violet-blues (negative)
    # Positives are u_norm > 0, Negatives are u_norm < 0
    # Center lines/shears get bright cyan highlight (where u_norm is close to zero, but active)
    grad_u = np.hypot(du_dx, du_dy)
    grad_norm = np.clip(grad_u * 12.0, 0.0, 1.0)
    
    # Map colors:
    # Warm embers
    r_warm = np.clip(u_norm * 255.0, 0, 255)
    g_warm = np.clip((u_norm ** 2) * 110.0, 0, 255)
    b_warm = np.clip((u_norm ** 3) * 20.0, 0, 255)
    
    # Cool obsidian voids
    r_cool = np.clip(-u_norm * 15.0, 0, 255)
    g_cool = np.clip(-u_norm * 5.0, 0, 255)
    b_cool = np.clip(-u_norm * 45.0, 0, 255)
    
    # Combine warm and cool states
    r_base = np.where(u_norm > 0, r_warm, r_cool)
    g_base = np.where(u_norm > 0, g_warm, g_cool)
    b_base = np.where(u_norm > 0, b_warm, b_cool)
    
    # Accent (cyan highlight at shear zones/boundaries where u changes sign)
    accent_mask = (1.0 - np.abs(u_norm)) * grad_norm
    r_out = (1.0 - accent_mask) * r_base + accent_mask * 0.0
    g_out = (1.0 - accent_mask) * g_base + accent_mask * 230.0
    b_out = (1.0 - accent_mask) * b_base + accent_mask * 255.0
    
    colored[..., 0] = np.clip(r_out, 0, 255).astype(np.uint8)
    colored[..., 1] = np.clip(g_out, 0, 255).astype(np.uint8)
    colored[..., 2] = np.clip(b_out, 0, 255).astype(np.uint8)
    
    py5.background(0)
    
    # Display the simulation scaled to output size (letterbox to 16:9)
    img = py5.create_image(W_sim, H_sim, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = colored
        img.update_np_pixels()
    else:
        r = colored[..., 0].astype(np.int32)
        g = colored[..., 1].astype(np.int32)
        b = colored[..., 2].astype(np.int32)
        a = colored[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()
    
    scale_w = py5.width
    scale_h = int(W_sim * (scale_w / W_sim))  # Scales proportionally
    scale_h = py5.height
    
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frame
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
