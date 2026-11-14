"""cymatic_salt_nodals — Chladni Nodal Lattices & Acoustic Resonance

An animation of standing acoustic waves on a dark anodized brass-slate plate
driving thousands of fine ivory silica, warm amber-gold, and vermilion garnet
sand grains into evolving Chladni nodal lattices. As the harmonic mode numbers
(n, m) sweep smoothly through non-integer couplings and the plate's acoustic
coupling shifts across four corners, nodal corridors unzip, bifurcate, and
re-crystallize into intricate resonant networks.

100% pure visual art — zero text, zero HUD panels.
"""

from __future__ import annotations

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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 21
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1260 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Modes sequence (n1, m1, n2, m2, coupling_angle) across the 21s timeline
MODE_KEYFRAMES = [
    (2.0, 5.0, 5.0, 2.0, 0.35),
    (3.0, 7.0, 7.0, 3.0, -0.45),
    (4.0, 9.0, 6.0, 5.0, 0.52),
    (5.0, 8.0, 8.0, 3.0, -0.38),
    (3.0, 6.0, 9.0, 4.0, 0.42),
]

fx = PostFX(
    bloom=0.28,
    bloom_threshold=0.72,
    tonemap=0.94,
    vignette=0.18,
    grain=0.018,
)

_shader = None
_rng = None
_px = None
_py = None
_vx = None
_vy = None
_ptype = None
_psize = None


def _ease_in_out_cubic(x: float) -> float:
    return 4.0 * x * x * x if x < 0.5 else 1.0 - (-2.0 * x + 2.0) ** 3 / 2.0


def _chladni_field_and_grad(x, y, n1, m1, n2, m2, mix_a, mix_b, phase_shift):
    """Compute standing wave amplitude W(x, y) and gradient of |W|."""
    pi = np.pi
    kx1 = n1 * pi * x
    ky1 = m1 * pi * y
    kx2 = m1 * pi * x
    ky2 = n1 * pi * y

    kx3 = n2 * pi * x + phase_shift
    ky3 = m2 * pi * y - phase_shift * 0.7
    kx4 = m2 * pi * x - phase_shift * 0.5
    ky4 = n2 * pi * y + phase_shift

    cx1, sx1 = np.cos(kx1), np.sin(kx1)
    cy1, sy1 = np.cos(ky1), np.sin(ky1)
    cx2, sx2 = np.cos(kx2), np.sin(kx2)
    cy2, sy2 = np.cos(ky2), np.sin(ky2)

    cx3, sx3 = np.cos(kx3), np.sin(kx3)
    cy3, sy3 = np.cos(ky3), np.sin(ky3)
    cx4, sx4 = np.cos(kx4), np.sin(kx4)
    cy4, sy4 = np.cos(ky4), np.sin(ky4)

    w1 = cx1 * cy1 - mix_a * cx2 * cy2
    dw1_dx = -n1 * pi * sx1 * cy1 + mix_a * m1 * pi * sx2 * cy2
    dw1_dy = -m1 * pi * cx1 * sy1 + mix_a * n1 * pi * cx2 * sy2

    w2 = cx3 * cy3 + mix_b * cx4 * cy4
    dw2_dx = -n2 * pi * sx3 * cy3 - mix_b * m2 * pi * sx4 * cy4
    dw2_dy = -m2 * pi * cx3 * sy3 - mix_b * n2 * pi * cx4 * sy4

    w = 0.68 * w1 + 0.32 * w2
    dw_dx = 0.68 * dw1_dx + 0.32 * dw2_dx
    dw_dy = 0.68 * dw1_dy + 0.32 * dw2_dy

    inv_norm = 1.0 / np.sqrt(w * w + 0.025)
    gx = w * dw_dx * inv_norm
    gy = w * dw_dy * inv_norm
    return np.abs(w), gx, gy


def _interp_modes(t: float):
    """Interpolate smoothly across MODE_KEYFRAMES for normalized time t in [0, 1]."""
    num_seg = len(MODE_KEYFRAMES) - 1
    scaled = min(max(t * num_seg, 0.0), num_seg - 1e-6)
    idx = int(scaled)
    frac = _ease_in_out_cubic(scaled - idx)
    k0 = MODE_KEYFRAMES[idx]
    k1 = MODE_KEYFRAMES[idx + 1]
    return tuple(k0[i] + (k1[i] - k0[i]) * frac for i in range(5))


def _draw_grain_batch(cx, cy, hs, r, g, b, a):
    """Vectorized quad rendering for thousands of sand grains."""
    n = len(cx)
    if n == 0:
        return
    verts = np.empty((n * 4, 2), dtype=np.float32)
    verts[0::4, 0] = cx - hs
    verts[0::4, 1] = cy - hs
    verts[1::4, 0] = cx + hs
    verts[1::4, 1] = cy - hs
    verts[2::4, 0] = cx + hs
    verts[2::4, 1] = cy + hs
    verts[3::4, 0] = cx - hs
    verts[3::4, 1] = cy + hs

    py5.fill(r, g, b, a)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(verts)


def setup() -> None:
    global _shader, _rng, _px, _py, _vx, _vy, _ptype, _psize
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _rng = np.random.default_rng()
    _shader = load_shader(SKETCH_DIR / "cymatic_salt_nodals.glsl")
    fx.setup()

    n_particles = 22000
    aspect = SIZE[0] / SIZE[1]

    # Seed initial positions along the boundary and scattered across the plate
    boundary_ratio = 0.45
    n_bound = int(n_particles * boundary_ratio)
    n_inner = n_particles - n_bound

    perim_t = _rng.uniform(0.0, 4.0, n_bound).astype(np.float32)
    bx = np.empty(n_bound, dtype=np.float32)
    by = np.empty(n_bound, dtype=np.float32)
    for side in range(4):
        mask = (perim_t >= side) & (perim_t < side + 1)
        u = (perim_t[mask] - side) * 2.0 - 1.0
        inward = _rng.exponential(0.16, np.sum(mask)).astype(np.float32)
        if side == 0:
            bx[mask] = u * aspect
            by[mask] = -1.0 + inward
        elif side == 1:
            bx[mask] = aspect - inward
            by[mask] = u
        elif side == 2:
            bx[mask] = u * aspect
            by[mask] = 1.0 - inward
        else:
            bx[mask] = -aspect + inward
            by[mask] = u

    ix = _rng.uniform(-aspect * 0.96, aspect * 0.96, n_inner).astype(np.float32)
    iy = _rng.uniform(-0.96, 0.96, n_inner).astype(np.float32)

    _px = np.concatenate([bx, ix])
    _py = np.concatenate([by, iy])
    _vx = np.zeros(n_particles, dtype=np.float32)
    _vy = np.zeros(n_particles, dtype=np.float32)

    # Grain classes: 0 = fine ivory silica (72%), 1 = warm gold brass (19%), 2 = vermilion garnet accent (9%)
    r_class = _rng.random(n_particles)
    _ptype = np.zeros(n_particles, dtype=np.int32)
    _ptype[r_class > 0.72] = 1
    _ptype[r_class > 0.91] = 2

    _psize = _rng.uniform(2.2, 5.2, n_particles).astype(np.float32)
    _psize[_ptype == 2] *= 1.25

    # Pre-settle 18 steps into initial mode so frame 1 already shows emergent boundary nodal filaments
    n1, m1, n2, m2, coup = _interp_modes(0.0)
    for _ in range(18):
        _, gx, gy = _chladni_field_and_grad(_px / aspect, _py, n1, m1, n2, m2, 0.85, 0.45, coup)
        _px -= gx * 0.0038 + _rng.normal(0.0, 0.0018, n_particles).astype(np.float32)
        _py -= gy * 0.0038 + _rng.normal(0.0, 0.0018, n_particles).astype(np.float32)
        _px = np.clip(_px, -aspect * 0.985, aspect * 0.985)
        _py = np.clip(_py, -0.985, 0.985)


def draw() -> None:
    global _px, _py, _vx, _vy
    fc = py5.frame_count
    t = (fc - 1) / float(TOTAL_FRAMES)
    aspect = SIZE[0] / SIZE[1]
    w_px, h_px = float(SIZE[0]), float(SIZE[1])

    n1, m1, n2, m2, coup = _interp_modes(t)
    mix_a = float(0.82 + 0.16 * np.sin(t * np.pi * 4.0 + 0.4))
    mix_b = float(0.48 + 0.28 * np.cos(t * np.pi * 3.0 - 0.6))
    phase_shift = float(coup + 0.35 * np.sin(t * np.pi * 2.0))

    # 1. Render continuous acoustic standing wave & nodal shimmer plate via GLSL
    draw_fullscreen(
        _shader,
        n1=float(n1),
        m1=float(m1),
        n2=float(n2),
        m2=float(m2),
        mixA=mix_a,
        mixB=mix_b,
        phaseShift=phase_shift,
    )

    # 2. Update sand grain advection toward zero-amplitude Chladni nodal curves
    amp, gx, gy = _chladni_field_and_grad(_px / aspect, _py, n1, m1, n2, m2, mix_a, mix_b, phase_shift)

    jitter_scale = (0.0005 + 0.0042 * amp).astype(np.float32)
    jx = _rng.normal(0.0, 1.0, len(_px)).astype(np.float32) * jitter_scale
    jy = _rng.normal(0.0, 1.0, len(_py)).astype(np.float32) * jitter_scale

    tangent_speed = 0.00042 * np.sin(t * np.pi * 6.0 + (_px * 2.0 + _py * 2.0))
    tx = -gy * tangent_speed
    ty = gx * tangent_speed

    _vx = _vx * 0.72 - gx * 0.0029 + tx + jx
    _vy = _vy * 0.72 - gy * 0.0029 + ty + jy
    _px += _vx
    _py += _vy

    # Respawn grains that drift out of bounds back near plate boundaries
    out_mask = (np.abs(_px) > aspect * 0.985) | (np.abs(_py) > 0.985)
    n_out = int(np.sum(out_mask))
    if n_out > 0:
        side = _rng.integers(0, 4, size=n_out)
        u = _rng.uniform(-0.96, 0.96, size=n_out).astype(np.float32)
        inward = _rng.uniform(0.015, 0.08, size=n_out).astype(np.float32)
        nx = np.where(side == 0, u * aspect, np.where(side == 1, aspect - inward, np.where(side == 2, u * aspect, -aspect + inward)))
        ny = np.where(side == 0, -1.0 + inward, np.where(side == 1, u, np.where(side == 2, 1.0 - inward, u)))
        _px[out_mask] = nx
        _py[out_mask] = ny
        _vx[out_mask] = 0.0
        _vy[out_mask] = 0.0

    # Convert particle coordinates to screen space and batch-render via vectorized QUADS
    sx = (_px / aspect * 0.5 + 0.5) * w_px
    sy = (_py * 0.5 + 0.5) * h_px

    node_lock = np.clip(1.0 - amp * 1.35, 0.15, 1.0)
    half_s = _psize * (0.65 + 0.45 * node_lock) * 0.5

    py5.no_stroke()
    m0 = _ptype == 0
    _draw_grain_batch(sx[m0], sy[m0], half_s[m0], 238, 232, 216, 215)

    m1_mask = _ptype == 1
    _draw_grain_batch(sx[m1_mask], sy[m1_mask], half_s[m1_mask] * 1.12, 230, 172, 78, 230)

    m2_mask = _ptype == 2
    _draw_grain_batch(sx[m2_mask], sy[m2_mask], half_s[m2_mask] * 1.25, 244, 86, 56, 245)

    # 3. Apply PostFX finishing pass
    fx.apply()

    # 4. Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
