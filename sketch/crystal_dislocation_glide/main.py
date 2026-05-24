"""
crystal_dislocation_glide
=========================
The sudden, violent slipping of microscopic lattice defects through an atomic crystal
under immense pressure, visualizing the invisible physics of plastic deformation.

Uses a 2D Sine-Gordon (Frenkel-Kontorova) phase-field model.
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
PREVIEW_FRAME = 500                         # Good action around frame 500
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

GW, GH = 960, 540

# Physics parameters
D = 16.0       # Elastic stiffness (controls defect width)
dt = 0.1       # Time step
SUBSTEPS = 10  # Substeps per frame
gamma = 0.5    # Damping (phonons to heat)

# State arrays
_u = None
_v = None
_A_map = None
_stress_field = None
_noise_tex = None
_X = None
_Y = None


def setup_physics():
    global _u, _v, _A_map, _stress_field, _noise_tex, _X, _Y

    _u = np.zeros((GH, GW), dtype=np.float32)
    _v = np.zeros((GH, GW), dtype=np.float32)

    x = np.arange(GW, dtype=np.float32)
    y = np.arange(GH, dtype=np.float32)
    _X, _Y = np.meshgrid(x, y)

    np.random.seed(42)

    # Lattice strength (A)
    # Base strength 1.0, with solid solution strengthening noise
    _A_map = 1.0 + np.random.normal(0, 0.1, (GH, GW)).astype(np.float32)
    # Strong precipitates (pinning centers)
    precipitates = np.random.rand(GH, GW) < 0.002
    _A_map[precipitates] = 5.0

    # Stress field (F)
    # Two intersecting shear bands
    X_c = _X - GW / 2
    Y_c = _Y - GH / 2
    rot1 = X_c * 0.707 + Y_c * 0.707
    band1 = np.exp(- (rot1 / 40) ** 2)
    
    rot2 = -X_c * 0.707 + Y_c * 0.707
    band2 = np.exp(- (rot2 / 40) ** 2)

    _stress_field = np.maximum(band1, band2) * 0.6 + 0.6
    # Add static heterogeneity to stress
    _stress_field += np.random.normal(0, 0.05, (GH, GW)).astype(np.float32)

    # Pre-generate dynamic thermal noise texture
    _noise_tex = np.random.normal(0, 0.02, (GH, GW)).astype(np.float32)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    setup_physics()
    print(f"[{WORK_NAME}] Setup OK  canvas={SIZE[0]}x{SIZE[1]}")


def draw():
    global _u, _v, _noise_tex

    fc = py5.frame_count

    # Ramp up macroscopic stress over time
    # Yielding begins when F > A. 
    # Max stress_field is ~1.2. A is ~1.0.
    # So yielding starts when fc/400.0 * 1.2 > 1.0  => fc > 333
    F_base = fc / 400.0
    F = F_base * _stress_field

    for _ in range(SUBSTEPS):
        lap_u = (np.roll(_u, 1, axis=0) + np.roll(_u, -1, axis=0) +
                 np.roll(_u, 1, axis=1) + np.roll(_u, -1, axis=1) - 4 * _u)
        
        # Fast rolling noise
        _noise_tex = np.roll(_noise_tex, 7, axis=0)
        _noise_tex = np.roll(_noise_tex, 13, axis=1)

        _v += dt * (D * lap_u - _A_map * np.sin(_u) + F - gamma * _v + _noise_tex)
        _u += dt * _v

    # ── Rendering ──────────────────────────────────────────────────────────

    # 1. Atomic lattice visualization
    grid_scale = 1.0
    # Phase mapping: atoms are bright where cos(X + u) + cos(Y) is high
    atom_val = (np.cos(_X * grid_scale + _u) + np.cos(_Y * grid_scale)) * 2.0 - 0.5
    atom = np.clip(atom_val, 0, 1)

    # 2. Defect core (stacking fault)
    core = np.sin(_u / 2.0) ** 2
    core = core ** 4  # tighten the visual core size

    # 3. Kinetic energy (phonons)
    kinetic = np.abs(_v)
    kin_norm = np.clip(kinetic * 1.5, 0, 1)

    # 4. Color mixing
    # Base: Deep Indigo
    # Atom: Ice Blue (90, 130, 210)
    # Phonon: Amethyst (150, 50, 200)
    # Core: Blinding Amber (255, 180, 50)
    
    R = 10 + atom * 80 + kin_norm * 150 + core * 255
    G = 15 + atom * 120 + kin_norm * 50  + core * 180
    B = 35 + atom * 180 + kin_norm * 200 + core * 50

    R = np.clip(R, 0, 255).astype(np.uint8)
    G = np.clip(G, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)

    # ── Upscale if needed ──────────────────────────────────────────────────
    W, H = SIZE
    if W != GW or H != GH:
        # Simple nearest neighbor upscale via kron if integer multiple
        sx = W // GW
        sy = H // GH
        if sx > 0 and sy > 0:
            ones = np.ones((sy, sx), dtype=np.uint8)
            R = np.kron(R, ones)[:H, :W]
            G = np.kron(G, ones)[:H, :W]
            B = np.kron(B, ones)[:H, :W]

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
        
        # Save a backup mid snapshot in case PREVIEW_FRAME was missed
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")


py5.run_sketch()
