"""wavelet_quantizer_array — 2D Wavelet Subband Decomposition & Quantization Array.

A 4x3 full-canvas rhythmic matrix of frequency subbands where Walsh-Hadamard square
packets and discrete cosine harmonics undergo live dead-zone quantization, horizontal
packet slip, and chroma macroblock gating across a deep nocturnal monochrome field
with a single burnt-signal amber accent.

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

DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1080 frames (18s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

COLS = 4
ROWS = 3

fx = PostFX(
    bloom=0.26,
    bloom_threshold=0.66,
    aberration=0.0014,
    tonemap=0.92,
    vignette=0.18,
    grain=0.018,
)
_shader = None
_tile_params: list[dict] = []


def _init_tiles() -> None:
    """Precompute randomized wavelet packet overlay geometry for the 12 subband tiles."""
    global _tile_params
    rng = np.random.default_rng()
    _tile_params = []

    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            n_packets = int(rng.integers(22, 34))
            y_norm = rng.uniform(-0.41, 0.41, size=n_packets)
            x_base = rng.uniform(-0.38, 0.38, size=n_packets)
            w_span = rng.uniform(0.04, 0.22, size=n_packets)
            h_span = rng.uniform(0.008, 0.026, size=n_packets)
            freq = rng.integers(1, 4, size=n_packets).astype(np.float64)
            phase = rng.uniform(0.0, math.tau, size=n_packets)
            is_accent = rng.random(size=n_packets) < 0.24

            n_nodes = 18
            node_t = np.linspace(-0.42, 0.42, n_nodes)
            node_freq_x = float(rng.integers(2, 6))
            node_freq_y = float(rng.integers(2, 5))
            node_phase = float(rng.uniform(0.0, math.tau))

            _tile_params.append(
                {
                    "row": r,
                    "col": c,
                    "idx": idx,
                    "y_norm": y_norm,
                    "x_base": x_base,
                    "w_span": w_span,
                    "h_span": h_span,
                    "freq": freq,
                    "phase": phase,
                    "is_accent": is_accent,
                    "node_t": node_t,
                    "node_freq_x": node_freq_x,
                    "node_freq_y": node_freq_y,
                    "node_phase": node_phase,
                }
            )


def _draw_subband_overlays(u_loop: float, w: float, h: float) -> None:
    """Render crisp vector quantization staircase traces and bit-packet bars."""
    tile_w = w / COLS
    tile_h = h / ROWS
    theta = u_loop * math.tau

    py5.rect_mode(py5.CENTER)

    for tp in _tile_params:
        c = tp["col"]
        r = tp["row"]
        idx = tp["idx"]
        cx = (c + 0.5) * tile_w
        cy = h - (r + 0.5) * tile_h
        cell_phase = idx * 0.52359877

        # 1. Quantized Packet Bars (horizontal bit-run blocks)
        y_arr = tp["y_norm"] * tile_h
        slip_arr = (
            0.14
            * tile_w
            * np.sin(theta * tp["freq"] + tp["phase"] + cell_phase)
        )
        x_arr = tp["x_base"] * tile_w + slip_arr
        q_step = (tile_w * 0.84) / 16.0
        x_quant = np.round(x_arr / q_step) * q_step
        w_arr = tp["w_span"] * tile_w * (
            0.55 + 0.45 * np.cos(theta * 2.0 + tp["phase"])
        )
        h_arr = tp["h_span"] * tile_h
        gate_arr = np.sin(theta * tp["freq"] - tp["phase"])

        py5.no_stroke()
        for i in range(len(y_arr)):
            if gate_arr[i] < -0.15:
                continue
            px = cx + float(x_quant[i])
            py_coord = cy + float(y_arr[i])
            bw = max(6.0, float(w_arr[i]))
            bh = max(3.0, float(h_arr[i]))

            if tp["is_accent"][i]:
                py5.fill(255, 94, 36, 215)
                py5.rect(px, py_coord, bw, bh)
                py5.fill(236, 244, 255, 235)
                py5.rect(px - bw * 0.46, py_coord, 4.0, bh * 1.25)
            else:
                alpha = int(125 + 95 * (0.5 + 0.5 * gate_arr[i]))
                py5.fill(228, 238, 250, alpha)
                py5.rect(px, py_coord, bw, bh)

        # 2. Staircase Quantizer Transfer Curve across subband
        node_t = tp["node_t"]
        raw_wave = 0.34 * np.sin(
            node_t * math.pi * tp["node_freq_x"] + theta + tp["node_phase"]
        ) + 0.12 * np.cos(
            node_t * math.pi * tp["node_freq_y"] - theta * 2.0
        )
        q_wave = np.round(raw_wave * 9.0) / 9.0

        xs = cx + node_t * tile_w * 0.98
        ys_quant = cy + q_wave * tile_h * 0.88
        ys_raw = cy + raw_wave * tile_h * 0.88

        py5.stroke(255, 94, 36, 175)
        py5.stroke_weight(2.2)
        for i in range(len(xs)):
            py5.line(float(xs[i]), float(ys_raw[i]), float(xs[i]), float(ys_quant[i]))

        py5.no_fill()
        py5.stroke(232, 241, 252, 210)
        py5.stroke_weight(2.6)
        with py5.begin_shape():
            for i in range(len(xs) - 1):
                py5.vertex(float(xs[i]), float(ys_quant[i]))
                py5.vertex(float(xs[i + 1]), float(ys_quant[i]))
            py5.vertex(float(xs[-1]), float(ys_quant[-1]))

        py5.no_stroke()
        for i in range(len(xs)):
            if i % 3 == 0:
                py5.fill(255, 94, 36, 240)
                py5.rect(float(xs[i]), float(ys_quant[i]), 7.5, 7.5)
            else:
                py5.fill(232, 241, 252, 225)
                py5.rect(float(xs[i]), float(ys_quant[i]), 5.5, 5.5)

    py5.rect_mode(py5.CORNER)


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "wavelet_quantizer_array.glsl")
    fx.setup()
    _init_tiles()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_subband_overlays(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
