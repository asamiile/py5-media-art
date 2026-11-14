from __future__ import annotations

import math
from pathlib import Path
import random
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, step_animation_frame
from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.shaders import PostFX
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 19
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED_PHASE = random.uniform(0.0, math.tau)
CAM_YAW_OFFSET = random.uniform(-0.16, 0.16)

fx = PostFX(
    bloom=0.38,
    bloom_threshold=0.60,
    tonemap=0.95,
    vignette=0.18,
    grain=0.022,
)

# 3D Multi-Tiered Catenary Organza Ribbons (45 suspended ribbons across 3 vertical tiers x 88 warp nodes)
N_RIBBONS = 45
N_WARP = 88

U_GRID: np.ndarray
RIBBON_TIER: np.ndarray
RIBBON_Z_BASE: np.ndarray
RIBBON_Y_ANCHOR: np.ndarray
RIBBON_SAG: np.ndarray
RIBBON_HEIGHT: np.ndarray
RIBBON_PHASE: np.ndarray
RIBBON_PALETTE_GROUP: np.ndarray

# 12 pre-computed color & luminance bins across Saffron Amber, Celadon Organza, and Persimmon Coral
COLOR_BINS = [
    # Group 0: Luminous Saffron Amber Silk (#f29e2e)
    (118, 66, 20, 128),
    (184, 108, 30, 152),
    (242, 158, 46, 178),
    (255, 218, 124, 208),
    # Group 1: Pale Celadon Organza (#d8ece2)
    (42, 102, 92, 118),
    (92, 162, 146, 144),
    (176, 224, 206, 170),
    (232, 248, 238, 202),
    # Group 2: Warm Persimmon Coral (#e85a3c)
    (112, 34, 26, 128),
    (176, 56, 40, 154),
    (232, 90, 60, 180),
    (255, 162, 122, 210),
]


def _init_canopy_geometry() -> None:
    global U_GRID, RIBBON_TIER, RIBBON_Z_BASE, RIBBON_Y_ANCHOR
    global RIBBON_SAG, RIBBON_HEIGHT, RIBBON_PHASE, RIBBON_PALETTE_GROUP

    rng = np.random.default_rng()
    u = np.linspace(-1.0, 1.0, N_WARP, dtype=np.float32)[None, :]
    U_GRID = np.broadcast_to(u, (N_RIBBONS, N_WARP)).copy()

    # Sort ribbons back-to-front in Z so translucent silk curtains layer naturally
    z_sorted = np.linspace(-1750.0, 1150.0, N_RIBBONS, dtype=np.float32) + rng.uniform(
        -25.0, 25.0, size=N_RIBBONS
    ).astype(np.float32)
    RIBBON_Z_BASE = z_sorted[:, None]

    # Distribute ribbons across 3 vertical atrium tiers (upper vault, mid canopy, lower drape)
    idx = np.arange(N_RIBBONS)
    tier = idx % 3
    RIBBON_TIER = tier[:, None]

    tier_y = np.where(tier == 0, -680.0, np.where(tier == 1, -180.0, 320.0)).astype(np.float32)
    RIBBON_Y_ANCHOR = (tier_y + rng.uniform(-75.0, 75.0, size=N_RIBBONS)).astype(np.float32)[:, None]

    # Deep, sculptural catenary sag (480 to 820 units)
    RIBBON_SAG = rng.uniform(480.0, 820.0, size=(N_RIBBONS, 1)).astype(np.float32)
    RIBBON_HEIGHT = rng.uniform(52.0, 96.0, size=(N_RIBBONS, 1)).astype(np.float32)
    RIBBON_PHASE = rng.uniform(0.0, math.tau, size=(N_RIBBONS, 1)).astype(np.float32)

    # 52% Saffron Amber (0), 30% Celadon Organza (1), 18% Persimmon Coral (2)
    RIBBON_PALETTE_GROUP = np.where(idx % 5 == 0, 2, np.where(idx % 3 == 1, 1, 0))[:, None]


def _compute_3d_canopy_bins(t_sec: float) -> list[np.ndarray]:
    u = U_GRID
    z_norm = RIBBON_Z_BASE / 1750.0

    # Golden-ratio poly-rhythmic frequencies
    w1 = 1.40
    w2 = 1.40 * 1.6180339
    w3 = 1.40 * 0.6180339

    # True hyperbolic cosine catenary curve hanging downward (+Y in py5 screen coords)
    # At u = +/-1, catenary_drop = 0 (pinned high at the top/sides); at u = 0, catenary_drop = 1 (deep belly)
    k_cat = 1.75
    catenary_drop = (math.cosh(k_cat) - np.cosh(k_cat * u)) / (math.cosh(k_cat) - 1.0)

    # Asymmetric diagonal sweep + poly-rhythmic harmonic wave trains
    asym_tilt = 190.0 * u * np.sin(z_norm * 1.8 + SEED_PHASE)
    wave_y = (
        115.0 * np.sin(u * 4.8 - t_sec * w1 + z_norm * 3.2 + RIBBON_PHASE)
        + 68.0 * np.cos(u * 8.4 + t_sec * w2 - z_norm * 4.5 + SEED_PHASE)
        + 42.0 * np.sin((u - z_norm) * 6.0 - t_sec * w3)
    )
    belly_env = 0.22 + 0.78 * (np.maximum(0.0, np.cos(u * math.pi * 0.5)) ** 1.25)

    # Transverse silk billowing in Z
    wave_z = (
        78.0 * np.sin(u * 3.6 - t_sec * w2 + RIBBON_PHASE)
        + 48.0 * np.cos(u * 6.8 + t_sec * w1 + z_norm * 2.5)
    ) * belly_env

    span_x = 2480.0
    X = u * span_x + 38.0 * np.sin(z_norm * 3.0 + t_sec * 0.6)
    Y_top = RIBBON_Y_ANCHOR + catenary_drop * RIBBON_SAG + asym_tilt + wave_y * belly_env
    Z_top = RIBBON_Z_BASE + wave_z

    # Each suspended organza sheet has a vertical curtain drape thickness that tapers at the ends
    drape_h = RIBBON_HEIGHT * (0.35 + 0.65 * catenary_drop) * (
        1.0 + 0.28 * np.sin(u * 9.0 - t_sec * w1 + RIBBON_PHASE)
    )
    Y_bot = Y_top + drape_h
    Z_bot = Z_top + 26.0 * np.cos(u * 5.2 - t_sec * w2 + RIBBON_PHASE)

    # Tangent along the ribbon warp (u) and along the curtain drape (v)
    tx = X[:, 1:] - X[:, :-1]
    ty = 0.5 * ((Y_top[:, 1:] - Y_top[:, :-1]) + (Y_bot[:, 1:] - Y_bot[:, :-1]))
    tz = 0.5 * ((Z_top[:, 1:] - Z_top[:, :-1]) + (Z_bot[:, 1:] - Z_bot[:, :-1]))

    vx = np.zeros_like(tx)
    vy = 0.5 * ((Y_bot[:, :-1] - Y_top[:, :-1]) + (Y_bot[:, 1:] - Y_top[:, 1:]))
    vz = 0.5 * ((Z_bot[:, :-1] - Z_top[:, :-1]) + (Z_bot[:, 1:] - Z_top[:, 1:]))

    nx = ty * vz - tz * vy
    ny = tz * vx - tx * vz
    nz = tx * vy - ty * vx
    n_len = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-5
    nx /= n_len
    ny /= n_len
    nz /= n_len

    # Orbiting clerestory light vector + vertical atmospheric depth attenuation
    light_ang = t_sec * 0.30 + SEED_PHASE
    lx = math.cos(light_ang) * 0.58
    ly = -0.52
    lz = math.sin(light_ang) * 0.62

    ndotl = np.abs(nx * lx + ny * ly + nz * lz)
    fold_crest = np.clip(-ty / (np.sqrt(tx * tx + ty * ty + tz * tz) + 1e-5) * 0.5 + 0.5, 0.0, 1.0)
    lum = np.clip(ndotl * 0.68 + fold_crest * 0.38, 0.0, 0.999)
    shade_bin = (lum * 4.0).astype(np.int32)

    group_cell = np.broadcast_to(RIBBON_PALETTE_GROUP, shade_bin.shape)
    bin_idx = group_cell * 4 + shade_bin

    quads = np.empty((N_RIBBONS, N_WARP - 1, 4, 3), dtype=np.float32)
    quads[:, :, 0, 0] = X[:, :-1]
    quads[:, :, 0, 1] = Y_top[:, :-1]
    quads[:, :, 0, 2] = Z_top[:, :-1]

    quads[:, :, 1, 0] = X[:, 1:]
    quads[:, :, 1, 1] = Y_top[:, 1:]
    quads[:, :, 1, 2] = Z_top[:, 1:]

    quads[:, :, 2, 0] = X[:, 1:]
    quads[:, :, 2, 1] = Y_bot[:, 1:]
    quads[:, :, 2, 2] = Z_bot[:, 1:]

    quads[:, :, 3, 0] = X[:, :-1]
    quads[:, :, 3, 1] = Y_bot[:, :-1]
    quads[:, :, 3, 2] = Z_bot[:, :-1]

    flat_bins = bin_idx.ravel()
    flat_quads = quads.reshape(-1, 4, 3)

    binned_verts: list[np.ndarray] = []
    for b in range(len(COLOR_BINS)):
        mask = flat_bins == b
        if np.any(mask):
            binned_verts.append(flat_quads[mask].reshape(-1, 3))
        else:
            binned_verts.append(np.empty((0, 3), dtype=np.float32))
    return binned_verts


def _draw_viridian_color_field(w: float, h: float, t_sec: float) -> None:
    """Full-bleed saturated forest-viridian to Prussian-teal atmospheric gradient bands."""
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.no_stroke()
    n_bands = 32
    ys = np.linspace(0.0, h, n_bands + 1, dtype=np.float32)
    for i in range(n_bands):
        u = i / float(n_bands - 1)
        # Transition from deep Prussian teal at zenith (#0b2632) to rich forest viridian (#14443c)
        # with a warm amber-jade subsurface glow near the mid-atrium
        glow = math.exp(-((u - 0.52 - 0.08 * math.sin(t_sec * 0.25)) ** 2) / 0.12)
        r = int(11 + 14 * u + 22 * glow)
        g = int(38 + 32 * (1.0 - abs(u - 0.55)) + 26 * glow)
        b = int(50 + 16 * (1.0 - u) + 10 * glow)
        py5.fill(r, g, b)
        py5.rect(0.0, float(ys[i]), w, float(ys[i + 1] - ys[i] + 1.5))


def setup() -> None:
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    fx.setup()
    _init_canopy_geometry()


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    w, h = float(SIZE[0]), float(SIZE[1])

    # 1. Full-bleed Rich Saturated Forest-Viridian to Prussian-Teal Color Field
    _draw_viridian_color_field(w, h, t_sec)

    # 2. Configure 3D perspective & smooth spatial camera orbit through the 3-tier canopy atrium
    py5.push_matrix()
    fov = math.pi / 3.0
    camera_z = (h / 2.0) / math.tan(fov / 2.0)
    py5.perspective(fov, w / h, camera_z / 12.0, camera_z * 12.0)

    py5.translate(w * 0.5, h * 0.44, -360.0 + 160.0 * math.sin(t_sec * 0.30))
    py5.rotate_x(-0.14 + 0.09 * math.cos(t_sec * 0.24))
    py5.rotate_y(CAM_YAW_OFFSET + 0.24 * math.sin(t_sec * 0.20))
    py5.rotate_z(0.06 * math.sin(t_sec * 0.17))

    # 3. Render 3-tier 3D volumetric catenary organza ribbons with translucent silk blending
    binned_verts = _compute_3d_canopy_bins(t_sec)
    py5.no_stroke()
    for b, verts in enumerate(binned_verts):
        if len(verts) == 0:
            continue
        r, g, bl, al = COLOR_BINS[b]
        py5.fill(r, g, bl, al)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(verts)

    py5.pop_matrix()

    # 4. Apply PostFX finishing pass (soft bloom on sunlit saffron crests + filmic tone-map)
    fx.apply()

    # 5. Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
