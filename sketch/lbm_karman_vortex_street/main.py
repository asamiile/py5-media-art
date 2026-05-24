"""
lbm_karman_vortex_street
========================
Vectorized 2D Lattice Boltzmann Method (D2Q9) simulation.
Visualizes the Von Kármán vortex street in a turbulent fluid flow.
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

# ── constants ───────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS           # 900
PREVIEW_FRAME = 600
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# LBM Grid Resolution
GW, GH = 480, 270
SUBSTEPS = 40

# LBM Parameters
tau = 0.55
u0 = 0.1

cxs = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1], dtype=np.int32)
cys = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1], dtype=np.int32)
weights = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36], dtype=np.float32)

_F = None
_obstacle = None
_diverging_colors = None

def setup_physics():
    global _F, _obstacle, _diverging_colors

    print(f"[{WORK_NAME}] Initializing LBM grid {GW}x{GH}...")
    _F = np.zeros((GH, GW, 9), dtype=np.float32)

    # Add a tiny initial perturbation to trigger instability faster
    uy_init = np.random.normal(0, 0.01, (GH, GW))
    for i in range(9):
        cu = 3.0 * (cxs[i] * u0 + cys[i] * uy_init)
        _F[:, :, i] = weights[i] * (1.0 + cu + 0.5 * cu**2 - 1.5 * (u0**2 + uy_init**2))

    # Obstacle geometry (slightly off-center Y to break perfect symmetry)
    X, Y = np.meshgrid(np.arange(GW), np.arange(GH))
    _obstacle = (X - GW // 4)**2 + (Y - GH // 2 - 2)**2 < (GH // 10)**2

    # Diverging colormap for vorticity [-1.0 ... 0.0 ... 1.0]
    _diverging_colors = np.array([
        [255, 255, 255],   # -1.0  (White)
        [255, 150, 0],     # -0.66 (Magma Orange)
        [220, 20, 50],     # -0.33 (Crimson Red)
        [0, 10, 40],       #  0.0  (Deep Abyss Blue)
        [0, 150, 150],     #  0.33 (Teal)
        [0, 255, 255],     #  0.66 (Cyan)
        [255, 255, 255],   #  1.0  (White)
    ], dtype=np.float32)

    # Warmup the simulation to develop the vortex street before recording
    print(f"[{WORK_NAME}] Warming up fluid dynamics (3000 steps)...")
    for step in range(3000):
        lbm_step()
        if (step + 1) % 1000 == 0:
            print(f"[{WORK_NAME}] Warmup: {step + 1}/3000")


def lbm_step():
    global _F
    
    # 1. Drift (Streaming)
    for i in range(9):
        _F[:, :, i] = np.roll(_F[:, :, i], cxs[i], axis=1)
        _F[:, :, i] = np.roll(_F[:, :, i], cys[i], axis=0)
        
    # 2. Extract boundaries for bounce-back
    bndryF = _F[_obstacle, :]
    # Opposite directions
    bndryF = bndryF[:, [0, 3, 4, 1, 2, 7, 8, 5, 6]]
    
    # 3. Macroscopic properties
    rho = np.sum(_F, axis=2)
    ux = np.sum(_F * cxs, axis=2) / rho
    uy = np.sum(_F * cys, axis=2) / rho
    
    # 4. Open boundary conditions (Inflow/Outflow)
    ux[:, -1] = ux[:, -2]
    uy[:, -1] = uy[:, -2]
    rho[:, -1] = rho[:, -2]
    
    ux[:, 0] = u0
    uy[:, 0] = 0.0
    rho[:, 0] = 1.0
    
    # 5. Collision (Relaxation to Equilibrium)
    u_sq = ux**2 + uy**2
    for i in range(9):
        cu = 3.0 * (cxs[i] * ux + cys[i] * uy)
        Feq = rho * weights[i] * (1.0 + cu + 0.5 * cu**2 - 1.5 * u_sq)
        _F[:, :, i] += -(1.0 / tau) * (_F[:, :, i] - Feq)
        
    # Apply obstacle bounce-back
    _F[_obstacle, :] = bndryF
    
    # Enforce inflow/outflow directly on populations
    for i in range(9):
        cu = 3.0 * cxs[i] * u0
        _F[:, 0, i] = weights[i] * (1.0 + cu + 0.5 * cu**2 - 1.5 * u0**2)
        _F[:, -1, i] = _F[:, -2, i]

    return ux, uy


def map_vorticity(vort):
    # Scale vorticity
    v = np.clip(vort * 15.0, -1.0, 1.0)
    # Map from [-1, 1] to [0, 6]
    p = (v + 1.0) * 3.0
    
    idx = np.floor(p).astype(np.int32)
    idx = np.clip(idx, 0, 5)
    f = p - idx
    
    c1 = _diverging_colors[idx]
    c2 = _diverging_colors[idx + 1]
    
    f_expanded = f[..., None]
    return c1 * (1.0 - f_expanded) + c2 * f_expanded


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    setup_physics()
    print(f"[{WORK_NAME}] Setup OK  canvas={SIZE[0]}x{SIZE[1]}")


def draw():
    fc = py5.frame_count

    # ── Physics Integration ───────────────────────────────────────────────
    ux, uy = None, None
    for _ in range(SUBSTEPS):
        ux, uy = lbm_step()

    # ── Compute Vorticity ──────────────────────────────────────────────────
    # vorticity = dv/dx - du/dy
    dudy, _ = np.gradient(ux)
    _, dvdx = np.gradient(uy)
    vorticity = dvdx - dudy

    # ── Rendering ──────────────────────────────────────────────────────────
    rgb = map_vorticity(vorticity)
    rgb[_obstacle] = [0, 0, 0]

    R = rgb[:, :, 0].astype(np.uint8)
    G = rgb[:, :, 1].astype(np.uint8)
    B = rgb[:, :, 2].astype(np.uint8)

    # ── Upscale ────────────────────────────────────────────────────────────
    W, H = SIZE
    sx = max(1, W // GW)
    sy = max(1, H // GH)
    
    R = np.repeat(np.repeat(R, sy, axis=0), sx, axis=1)[:H, :W]
    G = np.repeat(np.repeat(G, sy, axis=0), sx, axis=1)[:H, :W]
    B = np.repeat(np.repeat(B, sy, axis=0), sx, axis=1)[:H, :W]

    # ── Write pixel buffer ─────────────────────────────────────────────────
    py5.load_np_pixels()
    ah, aw = py5.np_pixels.shape[:2]
    bh = min(ah, H)
    bw = min(aw, W)

    py5.np_pixels[:bh, :bw, 0] = 255
    py5.np_pixels[:bh, :bw, 1] = R[:bh, :bw]
    py5.np_pixels[:bh, :bw, 2] = G[:bh, :bw]
    py5.np_pixels[:bh, :bw, 3] = B[:bh, :bw]
    py5.update_np_pixels()

    # ── Lifecycle ──────────────────────────────────────────────────────────
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % FPS == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    if fc >= TOTAL_FRAMES:
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

py5.run_sketch()
