"""
ginzburg_landau_spiral_defects
==============================
Vectorized 2D simulation of the Complex Ginzburg-Landau Equation (CGLE).
Visualizes the spontaneous emergence of topological defects and rotating spiral waves.
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
PREVIEW_FRAME = 600                         # Spirals are fully formed
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# Compute resolution (upscaled for speed)
GW, GH = 960, 540

# CGLE Parameters (Stable meandering spirals)
D = 8.0
b = 0.5
c = 1.5
dt = 0.015
SUBSTEPS = 12

_A = None
_colors = None

def setup_physics():
    global _A, _colors

    _A = np.zeros((GH, GW), dtype=np.complex64)
    X, Y = np.meshgrid(np.arange(GW), np.arange(GH))

    # Seed 12 majestic spirals (topological defects)
    np.random.seed(42)
    for i in range(12):
        xc = np.random.randint(50, GW - 50)
        yc = np.random.randint(50, GH - 50)
        
        # Alternating topological charge (+1 or -1)
        charge = 1 if i % 2 == 0 else -1
        theta = np.arctan2(Y - yc, X - xc) * charge
        
        r = np.sqrt((X - xc)**2 + (Y - yc)**2)
        # Add localized spiral phase winding
        _A += np.exp(-r / 150.0) * np.exp(1j * theta) * 2.0

    # Add high-frequency noise to kick off secondary dynamics
    _A += np.random.normal(0, 0.05, _A.shape) + 1j * np.random.normal(0, 0.05, _A.shape)
    _A = _A.astype(np.complex64)

    # Synthwave palette for mapping complex phase
    _colors = np.array([
        [0, 255, 255],   # Cyan
        [255, 0, 255],   # Magenta
        [255, 200, 0],   # Gold
        [0, 255, 100],   # Emerald
        [0, 255, 255]    # wrap to Cyan
    ], dtype=np.float32)


def map_colors(phase_norm):
    """Maps a [0, 1) phase to the synthwave palette."""
    p = phase_norm * 4.0
    idx = np.floor(p).astype(np.int32)
    f = p - idx
    idx = idx % 4
    
    c1 = _colors[idx]
    c2 = _colors[idx + 1]
    
    f_expanded = f[..., None]
    return c1 * (1.0 - f_expanded) + c2 * f_expanded


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    setup_physics()
    print(f"[{WORK_NAME}] Setup OK  canvas={SIZE[0]}x{SIZE[1]}")


def draw():
    global _A
    fc = py5.frame_count

    # ── Physics Integration (FDTD) ─────────────────────────────────────────
    for _ in range(SUBSTEPS):
        # 2D Laplacian with periodic boundaries
        lap_A = (np.roll(_A, 1, axis=0) + np.roll(_A, -1, axis=0) +
                 np.roll(_A, 1, axis=1) + np.roll(_A, -1, axis=1) - 4 * _A)
        
        A_sq = np.abs(_A)**2
        _A += dt * (_A + D * (1 + 1j * b) * lap_A - (1 + 1j * c) * A_sq * _A)

    # ── Rendering ──────────────────────────────────────────────────────────
    phase = np.angle(_A)  # [-pi, pi]
    # Normalize phase to [0, 1) and animate it
    phase_norm = (phase / (2 * np.pi) + 0.5 + fc * 0.005) % 1.0

    # Get pure RGB color from phase
    rgb = map_colors(phase_norm)

    # Modulate brightness by amplitude (defects become black holes)
    mag = np.abs(_A)
    # Sharpen the drop-off so defects look incredibly deep
    bri = np.clip(mag ** 3, 0, 1.0)[..., None]
    
    rgb = rgb * bri

    R = rgb[:, :, 0].astype(np.uint8)
    G = rgb[:, :, 1].astype(np.uint8)
    B = rgb[:, :, 2].astype(np.uint8)

    # ── Upscale ────────────────────────────────────────────────────────────
    W, H = SIZE
    if W != GW or H != GH:
        sx = W // GW
        sy = H // GH
        if sx > 0 and sy > 0:
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
        
        # Save a backup snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
