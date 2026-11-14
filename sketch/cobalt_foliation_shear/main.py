"""cobalt_foliation_shear — Diagonal Reeb Foliation & Symplectic Shear Strata.

Full-canvas diagonally swept topological foliation across a rich saturated color
field of deep forest viridian (#0a3830), cobalt ultramarine (#132c66), burnt
sienna (#d94e28), cadmium gold (#f4b024), and warm ivory (#f6efe2). Over an
18-second (1080-frame) multi-act temporal evolution, parallel Reeb foliation
leaves nucleate along 9 sheared strata, fold through homoclinic saddle whorls,
and re-laminate into harmonic equilibrium.

100% pure visual media art — zero text, zero HUD panels, zero bezels.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, step_animation_frame
from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.shaders import PostFX, draw_fullscreen, load_shader
from lib.sizes import get_sizes

# ── Constants ──────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1080 frames (18s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

fx = PostFX(
    bloom=0.18,
    bloom_threshold=0.76,
    aberration=0.0012,
    tonemap=0.26,
    vignette=0.12,
    grain=0.018,
)

# ── Diagonal Stratum Geometry Constants ────────────────────────────────
DIAG_ANGLE = 0.4712389  # ~27 deg matching GLSL
COS_A = math.cos(DIAG_ANGLE)
SIN_A = math.sin(DIAG_ANGLE)

N_STRATA = 9
LEAVES_PER_STRATUM = 18
N_RIBBONS = N_STRATA * LEAVES_PER_STRATUM  # 162 foliation leaf ribbons
N_PTS = 56

RIB_STRATUM: np.ndarray
RIB_V0: np.ndarray
RIB_S_OFFSET: np.ndarray
RIB_ROLE: np.ndarray
RIB_WIDTH: np.ndarray
S_PARAM: np.ndarray

foliation_shader = None


def _init_foliation() -> None:
    """Initialize Reeb foliation leaf parameters across the 9 diagonal strata."""
    global RIB_STRATUM, RIB_V0, RIB_S_OFFSET, RIB_ROLE, RIB_WIDTH, S_PARAM
    rng = np.random.default_rng()

    strata_ids = np.repeat(np.arange(-4, 5, dtype=np.float32), LEAVES_PER_STRATUM)
    v_local = np.tile(
        np.linspace(-0.42, 0.42, LEAVES_PER_STRATUM, dtype=np.float32),
        N_STRATA,
    )
    RIB_STRATUM = strata_ids
    RIB_V0 = v_local
    RIB_S_OFFSET = rng.uniform(0.0, math.tau, size=N_RIBBONS).astype(np.float32)

    # 3 visual color roles: 0 = Warm Ivory, 1 = Cadmium Gold, 2 = Coral-Vermilion
    RIB_ROLE = (np.arange(N_RIBBONS, dtype=np.int32) % 3)
    RIB_WIDTH = np.where(RIB_ROLE == 0, 2.3, np.where(RIB_ROLE == 1, 3.2, 2.8)).astype(
        np.float32
    )
    S_PARAM = np.linspace(-1.18, 1.18, N_PTS, dtype=np.float32)


def _diagonal_to_screen(s_val: np.ndarray, n_val: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map diagonal (s, n) coordinates in aspect-normalized space to screen pixels."""
    w, h = float(SIZE[0]), float(SIZE[1])
    aspect = w / h
    # Inverse rotation of q = R * p: p_x = cos*s - sin*n, p_y = sin*s + cos*n
    px = COS_A * s_val - SIN_A * n_val
    py = SIN_A * s_val + COS_A * n_val
    # Note: gl_FragCoord.y is bottom-up, screen Y is top-down
    sx = (px / aspect + 0.5) * w
    sy = (0.5 - py) * h
    return sx, sy


def _draw_foliation_overlays(u_loop: float, act_fold: float, act_shear: float) -> None:
    """Draw vectorized Reeb foliation leaf ribbons and saddle-node markers."""
    phase = u_loop * math.tau

    # Evaluate parametric curves for all 162 foliation ribbons: shape (N_RIBBONS, N_PTS)
    s_grid = S_PARAM[None, :]  # (1, N_PTS)
    band_idx = RIB_STRATUM[:, None]
    v0 = RIB_V0[:, None]
    dir_sign = (np.mod(band_idx, 2.0) * 2.0 - 1.0)

    # Advected coordinate along each diagonal stratum
    s_adv = s_grid * 4.2 + dir_sign * phase + RIB_S_OFFSET[:, None]

    # Reeb leaf transverse deflection (asymptotic near separatrix walls +/- 0.47)
    harmonic_wave = (
        (0.09 + 0.14 * act_fold)
        * np.sin(s_adv * 1.5 - dir_sign * phase)
        * (1.0 - 1.8 * v0 * v0)
    )
    whorl_mod = (
        0.065
        * act_shear
        * np.cos(s_grid * 7.5 + band_idx * 0.9 - phase * 2.0)
        * np.cos(v0 * math.pi)
    )
    v_trans = np.clip(v0 + harmonic_wave + whorl_mod, -0.465, 0.465)

    # Total normal coordinate n in diagonal space (6.5 strata per unit height)
    n_grid = (band_idx + 0.5 + v_trans) / 6.5

    sx, sy = _diagonal_to_screen(np.broadcast_to(s_grid, (N_RIBBONS, N_PTS)), n_grid)

    # Tangent and normal vectors along each ribbon
    dx = np.gradient(sx, axis=1)
    dy = np.gradient(sy, axis=1)
    inv_len = 1.0 / np.maximum(np.hypot(dx, dy), 1e-4)
    nx = -dy * inv_len
    ny = dx * inv_len

    # Taper ribbon width at ends
    env = np.clip(np.sin(np.linspace(0.0, math.pi, N_PTS, dtype=np.float32)), 0.0, 1.0)[None, :] ** 0.45
    hw = RIB_WIDTH[:, None] * (0.45 + 0.75 * env)

    x_up = sx + nx * hw
    y_up = sy + ny * hw
    x_dn = sx - nx * hw
    y_dn = sy - ny * hw

    quads = np.empty((N_RIBBONS, N_PTS - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_up[:, :-1]
    quads[:, :, 0, 1] = y_up[:, :-1]
    quads[:, :, 1, 0] = x_up[:, 1:]
    quads[:, :, 1, 1] = y_up[:, 1:]
    quads[:, :, 2, 0] = x_dn[:, 1:]
    quads[:, :, 2, 1] = y_dn[:, 1:]
    quads[:, :, 3, 0] = x_dn[:, :-1]
    quads[:, :, 3, 1] = y_dn[:, :-1]

    role_colors = (
        (246, 239, 226, 175),  # 0: Warm Ivory (#f6efe2)
        (244, 176, 36, 190),   # 1: Cadmium Gold (#f4b024)
        (240, 100, 56, 165),   # 2: Coral Vermilion (#f06438)
    )

    py5.no_stroke()
    for r_id, rgba in enumerate(role_colors):
        mask = RIB_ROLE == r_id
        verts = quads[mask].reshape(-1, 2)
        py5.fill(*rgba)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(verts)

    # Crisp hyperbolic saddle-point diamond markers along the separatrix boundaries
    n_sep_bays = 22
    s_nodes = np.linspace(-1.05, 1.05, n_sep_bays, dtype=np.float32)[None, :]
    b_borders = np.arange(-3, 4, dtype=np.float32)[:, None]
    s_shift = s_nodes + 0.08 * np.sin(b_borders * 1.4 + phase)
    n_borders = np.broadcast_to(b_borders / 6.5, s_shift.shape)

    bx, by = _diagonal_to_screen(s_shift, n_borders)
    bx_f = bx.reshape(-1)
    by_f = by.reshape(-1)
    rad = 4.8 + 2.4 * act_fold

    # Diamond quads aligned with the 27-deg diagonal shear axis
    ux, uy = COS_A * rad * 1.6, -SIN_A * rad * 1.6
    vx, vy = -SIN_A * rad * 0.9, -COS_A * rad * 0.9
    m_cnt = len(bx_f)
    d_quads = np.empty((m_cnt, 4, 2), dtype=np.float32)
    d_quads[:, 0, 0] = bx_f + ux
    d_quads[:, 0, 1] = by_f + uy
    d_quads[:, 1, 0] = bx_f + vx
    d_quads[:, 1, 1] = by_f + vy
    d_quads[:, 2, 0] = bx_f - ux
    d_quads[:, 2, 1] = by_f - uy
    d_quads[:, 3, 0] = bx_f - vx
    d_quads[:, 3, 1] = by_f - vy

    py5.fill(246, 239, 226, 215)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(d_quads.reshape(-1, 2))


def setup() -> None:
    global foliation_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    foliation_shader = load_shader(str(SKETCH_DIR / "cobalt_foliation_shear.glsl"))
    fx.setup()
    _init_foliation()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    phase = u_loop * math.tau

    # Multi-act temporal envelopes (seamless periodic over [0, TAU]):
    # Act I: Laminar shear | Act II: Peak homoclinic folding around u_loop=0.5 | Act III: Re-lamination
    act_fold = 0.5 - 0.5 * math.cos(phase)  # Peaks at 1.0 around middle of loop (preview frame!)
    act_shear = 0.5 + 0.5 * math.sin(phase * 2.0 - 0.6)

    foliation_shader.set("u_resolution", float(SIZE[0]), float(SIZE[1]))
    foliation_shader.set("u_phase", float(phase))
    foliation_shader.set("u_act_fold", float(act_fold))
    foliation_shader.set("u_act_shear", float(act_shear))
    draw_fullscreen(foliation_shader)

    _draw_foliation_overlays(u_loop, act_fold, act_shear)

    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
