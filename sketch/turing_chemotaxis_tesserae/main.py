"""turing_chemotaxis_tesserae — 5x3 Morphogenetic Reaction-Diffusion Tesserae & Wavefronts.

A full-canvas 5x3 rhythmic matrix of 15 morphogenetic reaction-diffusion tesserae
set on a mid-tone atmospheric dusk and celadon-slate ground (#2c3840 - #3d4e48).
Within each cellular domain, anisotropic activator-inhibitor Turing wavefronts and
450 chemotactic filament ribbons advect continuously along tilted shear axes in
soft chalk (#ebe6da), misty celadon (#82a8aa), warm amber-ochre (#e49636), and
terracotta (#ce5e40).

100% pure visual art — zero text, zero HUD panels.
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

DURATION_SEC = 19
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1140 frames (19s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

COLS = 5
ROWS = 3
N_CELLS = COLS * ROWS
RIBBONS_PER_CELL = 10
N_SEG_PTS = 36

fx = PostFX(
    bloom=0.20,
    bloom_threshold=0.72,
    aberration=0.0011,
    tonemap=0.52,
    vignette=0.14,
    grain=0.016,
)
_shader = None
_cells: list[dict] = []


def _init_cells() -> None:
    """Precompute 15 cellular morphogenetic flow parameters and advecting filaments."""
    global _cells
    rng = np.random.default_rng()
    _cells = []

    s_vals = np.linspace(-0.42, 0.42, N_SEG_PTS, dtype=np.float32)

    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            flow_ang = 0.35 * math.sin(idx * 1.1) + 0.22 * r - 0.18 * c
            v_offsets = np.linspace(-0.37, 0.37, RIBBONS_PER_CELL, dtype=np.float32)
            phases = rng.uniform(0.0, math.tau, size=RIBBONS_PER_CELL).astype(np.float32)
            roles = (np.arange(RIBBONS_PER_CELL) + idx) % 3

            # Chemotactic spore droplets advecting across the cell
            n_spores = 24
            sp_u0 = rng.uniform(-0.43, 0.43, size=n_spores).astype(np.float32)
            sp_v0 = rng.uniform(-0.39, 0.39, size=n_spores).astype(np.float32)
            sp_size = rng.uniform(4.2, 8.8, size=n_spores).astype(np.float32)
            sp_role = rng.integers(0, 3, size=n_spores)

            _cells.append(
                {
                    "row": r,
                    "col": c,
                    "idx": idx,
                    "flow_ang": flow_ang,
                    "s_vals": s_vals,
                    "v_offsets": v_offsets,
                    "phases": phases,
                    "roles": roles,
                    "sp_u0": sp_u0,
                    "sp_v0": sp_v0,
                    "sp_size": sp_size,
                    "sp_role": sp_role,
                }
            )


def _build_ribbon_quads(
    sx: np.ndarray, sy: np.ndarray, half_t: np.ndarray
) -> np.ndarray:
    """Build QUADS array from screen-space polyline (sx, sy) and half-thickness."""
    dx = np.gradient(sx)
    dy = np.gradient(sy)
    norm = np.hypot(dx, dy) + 1e-6
    nx = -dy / norm * half_t
    ny = dx / norm * half_t

    x_top = sx + nx
    y_top = sy + ny
    x_bot = sx - nx
    y_bot = sy - ny

    quads = np.empty(((len(sx) - 1) * 4, 2), dtype=np.float32)
    quads[0::4, 0] = x_top[:-1]
    quads[0::4, 1] = y_top[:-1]
    quads[1::4, 0] = x_top[1:]
    quads[1::4, 1] = y_top[1:]
    quads[2::4, 0] = x_bot[1:]
    quads[2::4, 1] = y_bot[1:]
    quads[3::4, 0] = x_bot[:-1]
    quads[3::4, 1] = y_bot[:-1]
    return quads


def _draw_morphogenetic_tesserae(u_loop: float, w: float, h: float) -> None:
    """Render advecting reaction-diffusion wavefront ribbons and chemotactic spores in all 15 cells."""
    tile_w = w / COLS
    tile_h = h / ROWS
    theta = u_loop * math.tau

    # Mid-Tone Atmospheric Dusk / Celadon Slate accent roles:
    # 0 = Soft Chalk (#ebe6da)
    # 1 = Warm Amber-Ochre (#e49636)
    # 2 = Misty Celadon-Teal (#82a8aa)
    role_colors = [
        (235, 230, 218, 195),
        (228, 150, 54, 205),
        (130, 168, 170, 185),
    ]

    quads_by_role: list[list[np.ndarray]] = [[] for _ in range(3)]
    spores_by_role: list[list[tuple[float, float, float]]] = [[] for _ in range(3)]

    taper = np.clip(np.sin(np.linspace(0.0, math.pi, N_SEG_PTS, dtype=np.float32)), 0.0, 1.0) ** 0.5

    for cell in _cells:
        c = cell["col"]
        r = cell["row"]
        idx = cell["idx"]
        cx = (c + 0.5) * tile_w
        cy = h - (r + 0.5) * tile_h

        ang = cell["flow_ang"]
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        s = cell["s_vals"]
        cell_phase = idx * 0.418879

        for j in range(RIBBONS_PER_CELL):
            v0 = float(cell["v_offsets"][j])
            ph = float(cell["phases"][j])
            role_id = int(cell["roles"][j])

            # Traveling reaction-diffusion wave along s
            wave_v = v0 + 0.048 * np.sin(s * 9.5 - theta * 2.0 + ph + cell_phase)
            u_local = s * cos_a - wave_v * sin_a
            v_local = s * sin_a + wave_v * cos_a

            # Clip smoothly inside tile bounds
            sx = cx + u_local * tile_w * 0.90
            sy = cy + v_local * tile_h * 0.88

            pulse = 0.5 + 0.5 * np.cos(s * 12.0 - theta * 2.0 + ph)
            half_t = (1.3 + 2.4 * (pulse ** 2)) * taper
            quads_by_role[role_id].append(_build_ribbon_quads(sx, sy, half_t))

        # Advect chemotactic spore droplets continuously across each cell (1 period = 0.86)
        period = 0.86
        sp_u = np.mod(cell["sp_u0"] + u_loop * period + 0.43, period) - 0.43
        sp_v = cell["sp_v0"] + 0.036 * np.sin(sp_u * 10.0 - theta * 2.0 + cell_phase)

        sp_x = cx + (sp_u * cos_a - sp_v * sin_a) * tile_w * 0.88
        sp_y = cy + (sp_u * sin_a + sp_v * cos_a) * tile_h * 0.86

        for k in range(len(sp_u)):
            r_id = int(cell["sp_role"][k])
            spores_by_role[r_id].append(
                (float(sp_x[k]), float(sp_y[k]), float(cell["sp_size"][k]))
            )

    py5.no_stroke()
    for r_id, (rc, gc, bc, ac) in enumerate(role_colors):
        if quads_by_role[r_id]:
            py5.fill(rc, gc, bc, ac)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(np.concatenate(quads_by_role[r_id], axis=0))

    py5.rect_mode(py5.CENTER)
    for r_id, (rc, gc, bc, _) in enumerate(role_colors):
        py5.fill(rc, gc, bc, 220)
        for sx_p, sy_p, sz in spores_by_role[r_id]:
            py5.rect(sx_p, sy_p, sz, sz)
    py5.rect_mode(py5.CORNER)


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "turing_chemotaxis_tesserae.glsl")
    fx.setup()
    _init_cells()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_morphogenetic_tesserae(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
