"""harmonograph_slate_caustics — Rhythmic Harmonograph Polyptych & Persistent Trail Decay

An edge-to-edge hierarchical polyptych of 46 subdivided acoustic pendulum cells
across a mid-tone atmospheric dusk slate field (#2c3840). In each cell, coupled
tri-frequency damped harmonograph pendulums trace evolving Lissajous-caustic
envelopes in soft chalk (#e8e3d8), warm amber-ochre (#e29434), and misty teal
(#8ab2b4) over a persistent translucent frame-decay buffer.

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

# Hierarchical polyptych cell arrays
NUM_CELLS = 0
CELL_CX: np.ndarray
CELL_CY: np.ndarray
CELL_RX: np.ndarray
CELL_RY: np.ndarray
CELL_FX1: np.ndarray
CELL_FY1: np.ndarray
CELL_FX2: np.ndarray
CELL_FY2: np.ndarray
CELL_PH1: np.ndarray
CELL_PH2: np.ndarray
CELL_ROLE: np.ndarray
CELL_BORDER_QUADS: np.ndarray

SUBSTEPS_PER_FRAME = 28


def _build_border_quads(x0: float, y0: float, x1: float, y1: float, thick: float) -> list[list[float]]:
    """Return 4 thin border rectangle quads (each 4x2) for a polyptych cell frame."""
    return [
        [[x0, y0], [x1, y0], [x1, y0 + thick], [x0, y0 + thick]],
        [[x0, y1 - thick], [x1, y1 - thick], [x1, y1], [x0, y1]],
        [[x0, y0], [x0 + thick, y0], [x0 + thick, y1], [x0, y1]],
        [[x1 - thick, y0], [x1, y0], [x1, y1], [x1 - thick, y1]],
    ]


def _init_polyptych(w: float, h: float) -> None:
    global NUM_CELLS, CELL_CX, CELL_CY, CELL_RX, CELL_RY
    global CELL_FX1, CELL_FY1, CELL_FX2, CELL_FY2, CELL_PH1, CELL_PH2, CELL_ROLE, CELL_BORDER_QUADS
    rng = np.random.default_rng()

    # Base 6x4 rhythmic grid across the full 3840x2160 canvas, with selective 2x2 subdivision
    cols, rows = 6, 4
    cw = w / cols
    ch = h / rows
    pad = 10.0

    cells = []
    borders = []
    for r in range(rows):
        for c in range(cols):
            bx0 = c * cw
            by0 = r * ch
            # Subdivide ~35% of base cells into 2x2 sub-cells for multi-scale rhythmic matrix hierarchy
            if (r + c) % 3 == 1:
                scw = cw * 0.5
                sch = ch * 0.5
                for sr in range(2):
                    for sc in range(2):
                        x0 = bx0 + sc * scw + pad * 0.7
                        y0 = by0 + sr * sch + pad * 0.7
                        x1 = bx0 + (sc + 1) * scw - pad * 0.7
                        y1 = by0 + (sr + 1) * sch - pad * 0.7
                        cells.append((x0, y0, x1, y1))
                        borders.extend(_build_border_quads(x0, y0, x1, y1, 1.5))
            else:
                x0 = bx0 + pad
                y0 = by0 + pad
                x1 = bx0 + cw - pad
                y1 = by0 + ch - pad
                cells.append((x0, y0, x1, y1))
                borders.extend(_build_border_quads(x0, y0, x1, y1, 2.0))

    NUM_CELLS = len(cells)
    arr = np.array(cells, dtype=np.float32)
    CELL_CX = 0.5 * (arr[:, 0] + arr[:, 2])[:, None]
    CELL_CY = 0.5 * (arr[:, 1] + arr[:, 3])[:, None]
    CELL_RX = 0.43 * (arr[:, 2] - arr[:, 0])[:, None]
    CELL_RY = 0.43 * (arr[:, 3] - arr[:, 1])[:, None]

    # Harmonic frequency ratios (1:2, 2:3, 3:4, 3:5, 4:5, 5:6) + slow rotary counter-pendulum
    ratios = [(1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (3.0, 5.0), (4.0, 5.0), (5.0, 6.0), (2.0, 5.0), (3.0, 7.0)]
    fx1, fy1, fx2, fy2 = [], [], [], []
    for i in range(NUM_CELLS):
        ra, rb = ratios[i % len(ratios)]
        detune = rng.uniform(-0.018, 0.018)
        fx1.append(ra + detune)
        fy1.append(rb - detune)
        fx2.append(rng.choice([-1.0, 1.0, -2.0, 2.0]))
        fy2.append(rng.choice([1.0, -1.0, 2.0, -2.0]))

    CELL_FX1 = np.array(fx1, dtype=np.float32)[:, None]
    CELL_FY1 = np.array(fy1, dtype=np.float32)[:, None]
    CELL_FX2 = np.array(fx2, dtype=np.float32)[:, None]
    CELL_FY2 = np.array(fy2, dtype=np.float32)[:, None]
    CELL_PH1 = rng.uniform(0.0, math.tau, size=(NUM_CELLS, 1)).astype(np.float32)
    CELL_PH2 = rng.uniform(0.0, math.tau, size=(NUM_CELLS, 1)).astype(np.float32)

    # Role: 0 = Soft Chalk (#e8e3d8), 1 = Warm Amber Ochre (#e29434), 2 = Misty Celadon-Teal (#8ab2b4)
    CELL_ROLE = np.arange(NUM_CELLS) % 3
    CELL_BORDER_QUADS = np.array(borders, dtype=np.float32).reshape(-1, 2)


def _compute_harmonograph_ribbons(indices: np.ndarray, tau0: float, tau1: float, phase_drift: float, width_px: float) -> np.ndarray:
    """Compute ribbon quads for a slice of harmonograph parameter tau in [tau0, tau1]."""
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)

    tau_vec = np.linspace(tau0, tau1, SUBSTEPS_PER_FRAME, dtype=np.float32)[None, :]
    cx0 = CELL_CX[indices]
    cy0 = CELL_CY[indices]
    rx = CELL_RX[indices]
    ry = CELL_RY[indices]

    fx1 = CELL_FX1[indices]
    fy1 = CELL_FY1[indices]
    fx2 = CELL_FX2[indices]
    fy2 = CELL_FY2[indices]
    ph1 = CELL_PH1[indices] + phase_drift
    ph2 = CELL_PH2[indices] - phase_drift * 0.7

    # Breathing radial envelope so pendulums spiral inward and outward across the cell
    env = 0.72 + 0.26 * np.sin(tau_vec * 0.11 + ph1)

    px = cx0 + rx * env * (0.72 * np.sin(fx1 * tau_vec + ph1) + 0.28 * np.cos(fx2 * tau_vec + ph2))
    py = cy0 + ry * env * (0.72 * np.cos(fy1 * tau_vec - ph1 * 0.5) + 0.28 * np.sin(fy2 * tau_vec - ph2))

    dx = px[:, 1:] - px[:, :-1]
    dy = py[:, 1:] - py[:, :-1]
    seg_len = np.hypot(dx, dy) + 1e-4
    nx = -dy / seg_len
    ny = dx / seg_len
    nx = np.concatenate([nx, nx[:, -1:]], axis=1)
    ny = np.concatenate([ny, ny[:, -1:]], axis=1)

    half_w = width_px * 0.5
    x_top = px - nx * half_w
    y_top = py - ny * half_w
    x_bot = px + nx * half_w
    y_bot = py + ny * half_w

    m = len(indices)
    quads = np.empty((m, SUBSTEPS_PER_FRAME - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_top[:, :-1]
    quads[:, :, 0, 1] = y_top[:, :-1]
    quads[:, :, 1, 0] = x_bot[:, :-1]
    quads[:, :, 1, 1] = y_bot[:, :-1]
    quads[:, :, 2, 0] = x_bot[:, 1:]
    quads[:, :, 2, 1] = y_bot[:, 1:]
    quads[:, :, 3, 0] = x_top[:, 1:]
    quads[:, :, 3, 1] = y_top[:, 1:]
    return quads.reshape(-1, 2)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    w, h = float(SIZE[0]), float(SIZE[1])
    # Mid-Tone Atmospheric Dusk / Celadon Slate ground (#2c3840)
    py5.background(44, 56, 64)
    _init_polyptych(w, h)


def draw() -> None:
    fc = py5.frame_count
    w, h = float(SIZE[0]), float(SIZE[1])

    # On frame 1, pre-accumulate 24 historical slices so the canvas opens with rich caustic harmonograph envelopes
    n_passes = 24 if fc == 1 else 1
    base_step = fc - 1

    py5.no_stroke()
    for p_idx in range(n_passes):
        # Persistent Trail Accumulation & Decay via translucent mid-tone dusk slate veil
        py5.fill(44, 56, 64, 7)
        py5.rect(0.0, 0.0, w, h)

        step_num = base_step - (n_passes - 1 - p_idx)
        tau0 = step_num * 0.36
        tau1 = (step_num + 1) * 0.36
        phase_drift = step_num * 0.0085

        # Role 2: Misty Celadon-Teal (#8ab2b4)
        py5.fill(138, 178, 180, 145)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_compute_harmonograph_ribbons(np.flatnonzero(CELL_ROLE == 2), tau0, tau1, phase_drift, 3.0))

        # Role 0: Soft Chalk (#e8e3d8)
        py5.fill(232, 227, 216, 165)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_compute_harmonograph_ribbons(np.flatnonzero(CELL_ROLE == 0), tau0, tau1, phase_drift, 2.8))

        # Role 1: Warm Amber Ochre (#e29434)
        py5.fill(226, 148, 52, 185)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_compute_harmonograph_ribbons(np.flatnonzero(CELL_ROLE == 1), tau0, tau1, phase_drift, 3.2))

    # Crisp subtle cell register hairlines across the full-canvas polyptych
    py5.fill(138, 178, 180, 26)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(CELL_BORDER_QUADS)

    # Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
