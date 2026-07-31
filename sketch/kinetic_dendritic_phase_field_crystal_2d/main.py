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

# Grid resolution (16:9 ratio matching 3840x2160)
GRID_W, GRID_H = 640, 360
DX = 1.0
DT = 0.025
TAU = 1.0
W0 = 1.0
LAMBDA = 1.2
D_DIFF = 2.0
ANISO_M = 6  # 6-fold hexagonal symmetry
ANISO_EPS = 0.15  # Strong anisotropy for sharp dendritic arms
UNDERCOOL = -0.52
STEPS_PER_FRAME = 7

# Simulation state
phi = np.zeros((GRID_H, GRID_W), dtype=np.float64)
u = np.full((GRID_H, GRID_W), UNDERCOOL, dtype=np.float64)
freeze_time = np.full((GRID_H, GRID_W), -1.0, dtype=np.float32)


def laplacian(f):
    return (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
            np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 4.0 * f) / (DX * DX)


def grad(f):
    fx = (np.roll(f, -1, axis=1) - np.roll(f, 1, axis=1)) / (2.0 * DX)
    fy = (np.roll(f, -1, axis=0) - np.roll(f, 1, axis=0)) / (2.0 * DX)
    return fx, fy


def anisotropic_laplacian(p, frame):
    px, py = grad(p)
    theta = np.arctan2(py, px)
    rot = frame * 0.0015
    a = 1.0 + ANISO_EPS * np.cos(ANISO_M * (theta - rot))
    a2 = a * a
    fx = a2 * px
    fy = a2 * py
    div = (np.roll(fx, -1, axis=1) - np.roll(fx, 1, axis=1)) / (2.0 * DX) + \
          (np.roll(fy, -1, axis=0) - np.roll(fy, 1, axis=0)) / (2.0 * DX)
    return div


def sim_step(frame):
    global phi, u, freeze_time
    noise = (np.random.rand(GRID_H, GRID_W) - 0.5) * 0.08
    dphi_dt = (W0 * W0 / TAU) * anisotropic_laplacian(phi, frame) + \
              phi * (1.0 - phi) * (phi - 0.5 - LAMBDA * u + noise) / TAU
    phi_new = np.clip(phi + DT * dphi_dt, 0.0, 1.0)
    dphi = phi_new - phi
    u_new = u + DT * (D_DIFF * laplacian(u) + 1.0 * dphi)
    
    # Track freeze timestamp for growth ring contours
    just_frozen = (phi_new >= 0.5) & (freeze_time < 0)
    freeze_time[just_frozen] = float(frame)
    
    phi = phi_new
    u = u_new


def init_seed():
    global phi, u, freeze_time
    phi.fill(0.0)
    u.fill(UNDERCOOL)
    freeze_time.fill(-1.0)
    cy, cx = GRID_H // 2, GRID_W // 2
    r_seed = 4
    yy, xx = np.ogrid[:GRID_H, :GRID_W]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r_seed ** 2
    phi[mask] = 1.0
    u[mask] = 0.0
    freeze_time[mask] = 0.0


def render_to_pixels():
    sw, sh = SIZE[0], SIZE[1]
    
    gy = (np.linspace(0, GRID_H - 1, sh)).astype(np.int32)
    gx = (np.linspace(0, GRID_W - 1, sw)).astype(np.int32)
    
    p_sub = phi[np.ix_(gy, gx)].astype(np.float32)
    u_sub = u[np.ix_(gy, gx)].astype(np.float32)
    t_sub = freeze_time[np.ix_(gy, gx)].astype(np.float32)
    
    px, py = grad(phi)
    grad_mag = np.sqrt(px * px + py * py)
    g_sub = grad_mag[np.ix_(gy, gx)].astype(np.float32)
    g_max = float(np.percentile(grad_mag, 99.5)) + 1e-5
    g_norm = np.clip(g_sub / g_max, 0.0, 1.0)
    
    u_norm = np.clip((u_sub - UNDERCOOL) / (0.0 - UNDERCOOL + 1e-5), 0.0, 1.0)
    
    # Growth ring contours from freeze timestamp
    has_frozen = t_sub >= 0
    contour_pattern = np.zeros_like(p_sub)
    contour_pattern[has_frozen] = np.abs(np.sin(t_sub[has_frozen] * 0.15)) ** 3.0
    
    # Radiating thermal waves in liquid
    yy_grid, xx_grid = np.ogrid[:sh, :sw]
    dist_center = np.sqrt((xx_grid - sw/2)**2 + (yy_grid - sh/2)**2)
    thermal_waves = np.sin(dist_center * 0.03 - py5.frame_count * 0.05) * (1.0 - p_sub)
    
    # Palette blending
    # Background: Deep Void Navy (#030712) + Violet thermal haze + ripple waves
    # Crystal interior: Semi-transparent Glacial Cyan (#0284c7) + Golden growth rings (#f59e0b)
    # Interface: Glowing Frost White / Electric Cyan (#e0f2fe)
    
    r = 3.0 + u_norm * 80.0 + p_sub * 20.0 + contour_pattern * 200.0 + g_norm * 220.0
    g = 7.0 + u_norm * 40.0 + p_sub * 120.0 + contour_pattern * 150.0 + g_norm * 245.0 + thermal_waves * 15.0
    b = 18.0 + u_norm * 190.0 + p_sub * 180.0 + contour_pattern * 40.0 + g_norm * 255.0 + thermal_waves * 30.0
    
    r8 = np.clip(r, 0, 255).astype(np.uint8)
    g8 = np.clip(g, 0, 255).astype(np.uint8)
    b8 = np.clip(b, 0, 255).astype(np.uint8)
    
    argb = (np.int32(-16777216) |
            (r8.astype(np.int32) << 16) |
            (g8.astype(np.int32) << 8) |
            b8.astype(np.int32))
    return argb


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    init_seed()


def draw():
    for _ in range(STEPS_PER_FRAME):
        sim_step(py5.frame_count)
        
    argb = render_to_pixels()
    py5.load_pixels()
    py5.pixels[:] = argb.flatten()
    py5.update_pixels()
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
