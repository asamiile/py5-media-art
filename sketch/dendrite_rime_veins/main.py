"""dendrite_rime_veins — Boundary-Nucleated Rime Frost Dendrites & Depth Parallax.

Across a deep nocturnal indigo and charcoal color field (#0a0d14 - #161c28),
branching rime-frost dendrites and crystalline vein networks nucleate along all
four canvas boundaries and grow inward across three parallax depth planes. As a
spatial camera drifts through the stratified crystal planes, colliding filament
tips ignite with a single restrained warm amber-gold accent (#f59332).

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

DURATION_SEC = 21
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1260 frames (21s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

fx = PostFX(
    bloom=0.28,
    bloom_threshold=0.66,
    aberration=0.0012,
    tonemap=0.85,
    vignette=0.16,
    grain=0.016,
)
_shader = None

# 3 depth-parallax layers of boundary-nucleated dendritic trees
_trees: list[dict] = []


def _generate_dendrite_tree(
    rng: np.random.Generator,
    x0: float,
    y0: float,
    angle0: float,
    depth_layer: int,
) -> dict:
    """Recursively build a branching boundary-to-interior dendrite tree in normalized coords."""
    seg_x0 = []
    seg_y0 = []
    seg_x1 = []
    seg_y1 = []
    seg_gen = []
    seg_t0 = []
    seg_t1 = []
    tip_x = []
    tip_y = []
    tip_t = []

    # Stack items: (x, y, angle, length, generation, t_start)
    base_len = float(rng.uniform(0.085, 0.135)) * (0.78 + 0.18 * depth_layer)
    stack = [(x0, y0, angle0, base_len, 0, 0.0)]
    max_gen = 5

    while stack:
        cx, cy, ang, length, gen, t_s = stack.pop()
        # Subdivide each branch into 3 organic curved segments
        n_sub = 3
        sub_len = length / n_sub
        cur_x, cur_y, cur_ang = cx, cy, ang
        t_span = 0.16 + 0.03 * gen

        for s in range(n_sub):
            cur_ang += float(rng.normal(0.0, 0.11))
            nx = cur_x + math.cos(cur_ang) * sub_len
            ny = cur_y + math.sin(cur_ang) * sub_len
            t0 = t_s + (s / float(n_sub)) * t_span
            t1 = t_s + ((s + 1) / float(n_sub)) * t_span

            seg_x0.append(cur_x)
            seg_y0.append(cur_y)
            seg_x1.append(nx)
            seg_y1.append(ny)
            seg_gen.append(gen)
            seg_t0.append(t0)
            seg_t1.append(t1)
            cur_x, cur_y = nx, ny

        t_end = t_s + t_span
        if gen < max_gen:
            # Bifurcate or trifurcate at hexagonal / dendritic rime angles
            n_children = 2 if rng.random() < 0.72 else 3
            spread = float(rng.uniform(0.38, 0.64))
            for c_idx in range(n_children):
                if n_children == 2:
                    delta = spread if c_idx == 0 else -spread
                else:
                    delta = (c_idx - 1) * spread * 0.85
                child_ang = cur_ang + delta + float(rng.normal(0.0, 0.06))
                child_len = length * float(rng.uniform(0.68, 0.82))
                stack.append((cur_x, cur_y, child_ang, child_len, gen + 1, t_end))
        else:
            tip_x.append(cur_x)
            tip_y.append(cur_y)
            tip_t.append(t_end)

    return {
        "layer": depth_layer,
        "phase": float(rng.uniform(0.0, math.tau)),
        "x0": np.array(seg_x0, dtype=np.float32),
        "y0": np.array(seg_y0, dtype=np.float32),
        "x1": np.array(seg_x1, dtype=np.float32),
        "y1": np.array(seg_y1, dtype=np.float32),
        "gen": np.array(seg_gen, dtype=np.int32),
        "t0": np.array(seg_t0, dtype=np.float32),
        "t1": np.array(seg_t1, dtype=np.float32),
        "tip_x": np.array(tip_x, dtype=np.float32),
        "tip_y": np.array(tip_y, dtype=np.float32),
        "tip_t": np.array(tip_t, dtype=np.float32),
    }


def _init_network() -> None:
    """Seed 36 boundary-nucleated dendrite trees along all 4 canvas edges across 3 depth layers."""
    global _trees
    rng = np.random.default_rng()
    _trees = []

    for layer in range(3):
        n_seeds = 12
        for i in range(n_seeds):
            edge = i % 4
            u = float(rng.uniform(-0.46, 0.46))
            if edge == 0:  # Top boundary growing downward/inward
                x0, y0 = u * 1.78, -0.52
                ang0 = math.pi * 0.5 + float(rng.uniform(-0.42, 0.42))
            elif edge == 1:  # Bottom boundary growing upward/inward
                x0, y0 = u * 1.78, 0.52
                ang0 = -math.pi * 0.5 + float(rng.uniform(-0.42, 0.42))
            elif edge == 2:  # Left boundary growing rightward/inward
                x0, y0 = -0.92, u
                ang0 = 0.0 + float(rng.uniform(-0.42, 0.42))
            else:  # Right boundary growing leftward/inward
                x0, y0 = 0.92, u
                ang0 = math.pi + float(rng.uniform(-0.42, 0.42))

            _trees.append(_generate_dendrite_tree(rng, x0, y0, ang0, layer))


def _draw_dendrite_layers(u_loop: float, w: float, h: float) -> None:
    """Render 3 depth-parallax planes of boundary-to-interior dendritic filaments and amber tips."""
    theta = u_loop * math.tau
    cam_px = 0.045 * math.cos(theta)
    cam_py = 0.034 * math.sin(theta)

    # Layer styling: nocturnal graphite -> silver -> crisp frost white
    layer_colors = [
        (96, 114, 142, 135),   # Layer 0 (deep background parallax)
        (175, 194, 218, 175),  # Layer 1 (midplane parallax)
        (234, 243, 252, 215),  # Layer 2 (foreground crisp frost)
    ]
    layer_weights = [1.4, 2.1, 2.9]

    py5.rect_mode(py5.CENTER)

    for layer in range(3):
        fl = float(layer)
        z_scale = 1.0 + 0.14 * math.sin(theta + fl * 2.094)
        px_shift = cam_px * (0.55 + fl * 0.45) * h
        py_shift = cam_py * (0.55 + fl * 0.45) * h

        r_c, g_c, b_c, a_c = layer_colors[layer]
        base_w = layer_weights[layer]

        segs_by_gen: list[np.ndarray] = [[] for _ in range(6)]
        amber_tips_x = []
        amber_tips_y = []
        amber_tips_s = []

        for tr in _trees:
            if tr["layer"] != layer:
                continue

            # Cyclic boundary-to-interior growth wave: trees extend inward, crystallize, and breathe
            growth_reach = 0.72 + 0.34 * math.sin(theta - tr["phase"])
            active_mask = tr["t0"] < growth_reach
            if not np.any(active_mask):
                continue

            # Partial extension along frontier segments
            frac = np.clip((growth_reach - tr["t0"]) / (tr["t1"] - tr["t0"] + 1e-5), 0.0, 1.0)

            sx0 = w * 0.5 + tr["x0"] * h * z_scale + px_shift
            sy0 = h * 0.5 + tr["y0"] * h * z_scale + py_shift
            sx1_full = w * 0.5 + tr["x1"] * h * z_scale + px_shift
            sy1_full = h * 0.5 + tr["y1"] * h * z_scale + py_shift

            sx1 = sx0 + (sx1_full - sx0) * frac
            sy1 = sy0 + (sy1_full - sy0) * frac

            for g_idx in range(6):
                g_mask = active_mask & (tr["gen"] == g_idx)
                idx = np.flatnonzero(g_mask)
                if len(idx) > 0:
                    s_arr = np.empty((len(idx), 2, 2), dtype=np.float32)
                    s_arr[:, 0, 0] = sx0[idx]
                    s_arr[:, 0, 1] = sy0[idx]
                    s_arr[:, 1, 0] = sx1[idx]
                    s_arr[:, 1, 1] = sy1[idx]
                    segs_by_gen[g_idx].append(s_arr.reshape(-1, 2))

            # Active growing frontier nodes ignite with the single warm amber accent (#f59332)
            frontier_mask = (tr["t0"] < growth_reach) & (tr["t1"] >= growth_reach - 0.12)
            f_idx = np.flatnonzero(frontier_mask)
            for k in f_idx:
                amber_tips_x.append(float(sx1[k]))
                amber_tips_y.append(float(sy1[k]))
                amber_tips_s.append(4.5 + 2.5 * layer)

            # Terminal crystal tips when fully grown
            tip_mask = tr["tip_t"] <= growth_reach
            t_idx = np.flatnonzero(tip_mask)
            for k in t_idx:
                tx = w * 0.5 + float(tr["tip_x"][k]) * h * z_scale + px_shift
                ty = h * 0.5 + float(tr["tip_y"][k]) * h * z_scale + py_shift
                amber_tips_x.append(tx)
                amber_tips_y.append(ty)
                amber_tips_s.append(3.8 + 2.0 * layer)

        # Draw batched dendritic branches per generation with tapering stroke weight
        py5.no_fill()
        for g_idx in range(6):
            if not segs_by_gen[g_idx]:
                continue
            all_verts = np.concatenate(segs_by_gen[g_idx], axis=0)
            w_gen = max(0.85, base_w * (0.82 ** g_idx))
            alpha_gen = int(max(75, a_c * (0.92 ** g_idx)))
            py5.stroke(r_c, g_c, b_c, alpha_gen)
            py5.stroke_weight(w_gen)
            with py5.begin_shape(py5.LINES):
                py5.vertices(all_verts)

        # Draw single-accent warm amber gold (#f59332) nucleation/collision crystals
        py5.no_stroke()
        py5.fill(245, 147, 50, 215)
        for tx, ty, ts in zip(amber_tips_x, amber_tips_y, amber_tips_s):
            py5.rect(tx, ty, ts, ts)

    py5.rect_mode(py5.CORNER)


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "dendrite_rime_veins.glsl")
    fx.setup()
    _init_network()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_dendrite_layers(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

