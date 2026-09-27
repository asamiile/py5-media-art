"""
Smoke test for lib/shaders.py: renders each usage pattern headlessly-ish
(a window opens briefly), checks the result is not blank, and reports ms/frame.

  uv run python scripts/check_shaders.py            # all modes, 3840x2160
  uv run python scripts/check_shaders.py --mode p3d --size 1920x1080

Images are written to $TMPDIR/py5-media-art-shader-check/.
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(tempfile.gettempdir()) / "py5-media-art-shader-check"
MODES = ["field", "accumulate", "p3d", "align-screen", "align-canvas"]
FRAMES = 30


CFG: dict = {}
STATE: dict = {}


def settings():
    import py5

    py5.size(CFG["width"], CFG["height"], py5.P3D if CFG["mode"] == "p3d" else py5.P2D)
    py5.pixel_density(1)


def setup():
    import py5

    from lib.shaders import PostFX, load_shader

    if CFG["mode"].startswith("align"):
        # Bloom only, so any light away from the dot comes from a misaligned bloom texture.
        fx = STATE["fx"] = PostFX(bloom=1.0, bloom_threshold=0.5, vignette=0.0, grain=0.0)
    else:
        fx = STATE["fx"] = PostFX(bloom=0.9, tonemap=1.0, aberration=0.004, vignette=0.35, grain=0.04)
    fx.setup()
    if CFG["mode"] == "field":
        STATE["field"] = load_shader("field_example.glsl")
        STATE["seed"] = random.uniform(0, 1000)
    if CFG["mode"] in ("accumulate", "align-canvas"):
        c = STATE["canvas"] = fx.create_canvas()
        c.begin_draw()
        c.background(5, 6, 12)
        c.end_draw()
    STATE["t0"] = time.time()


def draw():
    import os

    import py5

    from lib.shaders import draw_fullscreen

    mode, fx = CFG["mode"], STATE["fx"]
    if mode == "field":
        draw_fullscreen(STATE["field"], colorA=(0.02, 0.03, 0.10), colorB=(0.85, 0.35, 0.20), seed=STATE["seed"])
        fx.apply()
    elif mode == "accumulate":
        c = STATE["canvas"]
        c.begin_draw()
        c.no_stroke()
        c.fill(5, 6, 12, 18)
        c.rect(0, 0, c.width, c.height)
        for i in range(40):
            a = py5.frame_count * 0.05 + i * 0.157
            c.fill(255, 180 + i * 2, 90, 220)
            c.circle(c.width / 2 + py5.cos(a * 1.3) * c.width * 0.3,
                     c.height / 2 + py5.sin(a) * c.height * 0.3, c.height * 0.02)
        c.end_draw()
        fx.apply(c)
    elif mode.startswith("align"):
        g = STATE["canvas"] if mode == "align-canvas" else py5
        if mode == "align-canvas":
            g.begin_draw()
        g.background(0)
        g.no_stroke()
        g.fill(255)
        g.circle(g.width * 0.25, g.height * 0.25, g.height * 0.05)
        if mode == "align-canvas":
            g.end_draw()
            fx.apply(g)
        else:
            fx.apply()
    else:
        py5.background(8, 10, 20)
        py5.lights()
        py5.translate(py5.width / 2, py5.height / 2, 0)
        py5.rotate_y(py5.frame_count * 0.03)
        py5.rotate_x(0.4)
        py5.no_stroke()
        py5.fill(255, 120, 60)
        py5.box(py5.height * 0.3)
        py5.fill(255)
        py5.sphere(py5.height * 0.08)
        fx.apply()

    if py5.frame_count == FRAMES:
        ms = (time.time() - STATE["t0"]) / FRAMES * 1000
        py5.load_np_pixels()
        std = float(py5.np_pixels.std())
        h, w = py5.np_pixels.shape[:2]
        OUT_DIR.mkdir(exist_ok=True)
        out = OUT_DIR / f"{mode}.png"
        py5.save_frame(str(out))
        ok = std > 1.0 and (w, h) == (CFG["width"], CFG["height"])
        if mode.startswith("align"):
            # Glow just below the dot vs. the same offset at the vertically mirrored spot.
            px = py5.np_pixels
            near = px[int(h * 0.25 + h * 0.04), int(w * 0.25), 1:].mean()
            mirrored = px[int(h * 0.75 + h * 0.04), int(w * 0.25), 1:].mean()
            print(f"  glow near dot={near:.0f}, at mirrored spot={mirrored:.0f}", flush=True)
            ok = ok and near > 8 and mirrored < 2
        print(f"[{'OK' if ok else 'FAIL'}] {mode}: {w}x{h} std={std:.1f} {ms:.0f} ms/frame -> {out}", flush=True)
        os._exit(0 if ok else 1)


def run_mode(mode: str, width: int, height: int) -> None:
    sys.path.append(str(PROJECT_ROOT))
    import py5

    CFG.update(mode=mode, width=width, height=height)
    py5.run_sketch(sketch_functions={"settings": settings, "setup": setup, "draw": draw})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--size", default="3840x2160")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    width, height = (int(v) for v in args.size.lower().split("x"))

    if args.child:
        run_mode(args.mode, width, height)
        return 0

    failed = []
    for mode in [args.mode] if args.mode else MODES:
        # A py5 error leaves the window open instead of exiting, so time out.
        try:
            code = subprocess.run(
                [sys.executable, __file__, "--child", "--mode", mode, "--size", args.size],
                timeout=120,
            ).returncode
        except subprocess.TimeoutExpired:
            code = "timeout (see the py5 error above)"
        if code != 0:
            print(f"[FAIL] {mode}: exit {code}")
            failed.append(mode)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
