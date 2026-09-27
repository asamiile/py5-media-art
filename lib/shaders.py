"""
GLSL shader helpers for py5 sketches (optional; see .agents/skills/shared/shaders.md).

Shaders need an OpenGL renderer: ``py5.size(w, h, py5.P2D)`` or ``py5.P3D``.

- ``load_shader(path)``: load a fragment shader, resolving ``#include "noise.glsl"``
  against the sketch folder and ``lib/glsl/``.
- ``draw_fullscreen(shader, **uniforms)``: run a fragment shader over the whole
  canvas (GPU fields: noise, fluids, interference, raymarching...).
- ``PostFX``: finishing pass (bloom, tone map, chromatic aberration, vignette,
  grain) applied to the screen or to an offscreen canvas.
"""

from __future__ import annotations

import hashlib
import re
import tempfile
from pathlib import Path
from typing import Any

GLSL_DIR = Path(__file__).resolve().parent / "glsl"
_INCLUDE = re.compile(r'^\s*#include\s+"([^"]+)"\s*$', re.MULTILINE)


def _resolve_includes(source: str, search: list[Path], seen: set[Path]) -> str:
    def replace(match: re.Match) -> str:
        for base in search:
            candidate = (base / match[1]).resolve()
            if candidate.exists():
                if candidate in seen:
                    return ""
                seen.add(candidate)
                return _resolve_includes(candidate.read_text(), search, seen)
        raise FileNotFoundError(f'#include "{match[1]}" not found in {[str(s) for s in search]}')

    return _INCLUDE.sub(replace, source)


def _materialize(path: Path) -> str:
    """Return a file path py5 can load, with #include lines expanded."""
    source = path.read_text()
    if not _INCLUDE.search(source):
        return str(path)
    expanded = _resolve_includes(source, [path.parent, GLSL_DIR], {path.resolve()})
    digest = hashlib.sha1(expanded.encode()).hexdigest()[:12]
    out = Path(tempfile.gettempdir()) / "py5-media-art-glsl" / f"{path.stem}-{digest}.glsl"
    out.parent.mkdir(exist_ok=True)
    out.write_text(expanded)
    return str(out)


def load_shader(frag: str | Path, vert: str | Path | None = None, graphics: Any = None):
    """
    Load a shader. A bare name ("finish.glsl") is looked up in lib/glsl/.
    ``graphics`` loads it for an offscreen Py5Graphics instead of the main canvas.
    """
    import py5

    def locate(p: str | Path) -> Path:
        p = Path(p)
        if not p.is_absolute() and not p.exists() and (GLSL_DIR / p).exists():
            p = GLSL_DIR / p
        if not p.exists():
            raise FileNotFoundError(p)
        return p

    loader = graphics.load_shader if graphics is not None else py5.load_shader
    frag_path = _materialize(locate(frag))
    if vert is None:
        return loader(frag_path)
    return loader(frag_path, _materialize(locate(vert)))


def set_uniforms(shader, **uniforms) -> None:
    """Set uniforms; tuples/lists become vecN, bools become ints."""
    for name, value in uniforms.items():
        if isinstance(value, bool):
            shader.set(name, int(value))
        elif isinstance(value, (tuple, list)):
            shader.set(name, *[float(v) for v in value])
        elif isinstance(value, (int, float)):
            shader.set(name, float(value))
        else:
            shader.set(name, value)  # textures (Py5Graphics / Py5Image) etc.


def draw_fullscreen(shader, graphics: Any = None, **uniforms) -> None:
    """
    Fill the canvas (or ``graphics``) with a fragment shader.
    ``resolution`` (vec2, pixels) and ``time`` (seconds at 60 fps) are set automatically.
    """
    import py5

    g = graphics if graphics is not None else py5
    set_uniforms(
        shader,
        resolution=(g.width, g.height),
        time=py5.frame_count / 60.0,
        **uniforms,
    )
    g.push_style()
    g.shader(shader)
    g.no_stroke()
    g.fill(255)
    g.rect(0, 0, g.width, g.height)
    g.reset_shader()
    g.pop_style()


class PostFX:
    """
    Finishing pass. Call ``setup()`` after ``py5.size(..., py5.P2D/P3D)``, then
    ``apply()`` at the end of ``draw()`` (before saving the frame).

    - Sketches that redraw the background every frame: ``fx.apply()`` filters the
      screen in place.
    - Sketches that accumulate (no background each frame): draw into an offscreen
      canvas from ``fx.create_canvas()`` and call ``fx.apply(canvas)``; the screen
      then shows the processed copy while the canvas keeps the raw accumulation.

    Every effect is off at 0; defaults are subtle.
    """

    def __init__(
        self,
        *,
        bloom: float = 0.6,
        bloom_threshold: float = 0.6,
        bloom_knee: float = 0.2,
        bloom_radius: float = 1.0,
        bloom_passes: int = 3,
        bloom_scale: int = 4,
        exposure: float = 1.0,
        tonemap: float = 0.0,
        aberration: float = 0.0,
        vignette: float = 0.25,
        grain: float = 0.03,
        saturation: float = 1.0,
        enabled: bool = True,
    ) -> None:
        self.bloom = bloom
        self.bloom_threshold = bloom_threshold
        self.bloom_knee = bloom_knee
        self.bloom_radius = bloom_radius
        self.bloom_passes = bloom_passes
        self.bloom_scale = bloom_scale
        self.exposure = exposure
        self.tonemap = tonemap
        self.aberration = aberration
        self.vignette = vignette
        self.grain = grain
        self.saturation = saturation
        self.enabled = enabled
        self._ready = False

    def setup(self) -> None:
        import py5

        w = max(1, py5.width // self.bloom_scale)
        h = max(1, py5.height // self.bloom_scale)
        self._ping = py5.create_graphics(w, h, py5.P2D)
        self._pong = py5.create_graphics(w, h, py5.P2D)
        for g in (self._ping, self._pong):
            # Creates the GL context; loading a shader before this fails.
            g.begin_draw()
            g.background(0)
            g.end_draw()
        self._extract = load_shader("bloom_extract.glsl", graphics=self._ping)
        self._blur_ping = load_shader("blur.glsl", graphics=self._ping)
        self._blur_pong = load_shader("blur.glsl", graphics=self._pong)
        self._finish = load_shader("finish.glsl")
        self._ready = True

    def create_canvas(self, renderer=None):
        """Offscreen full-size canvas for accumulating sketches."""
        import py5

        canvas = py5.create_graphics(py5.width, py5.height, renderer or py5.P2D)
        canvas.begin_draw()
        canvas.end_draw()
        return canvas

    def _bloom_pass(self, source) -> None:
        ping, pong = self._ping, self._pong
        set_uniforms(self._extract, threshold=self.bloom_threshold, knee=self.bloom_knee)
        ping.begin_draw()
        ping.shader(self._extract)
        ping.image(source, 0, 0, ping.width, ping.height)
        ping.reset_shader()
        ping.end_draw()
        for i in range(self.bloom_passes):
            spread = self.bloom_radius * (1.0 + i)
            set_uniforms(self._blur_pong, direction=(spread, 0.0))
            pong.begin_draw()
            pong.shader(self._blur_pong)
            pong.image(ping, 0, 0)
            pong.reset_shader()
            pong.end_draw()
            set_uniforms(self._blur_ping, direction=(0.0, spread))
            ping.begin_draw()
            ping.shader(self._blur_ping)
            ping.image(pong, 0, 0)
            ping.reset_shader()
            ping.end_draw()

    def apply(self, source: Any = None) -> None:
        """Process ``source`` (an offscreen canvas) to the screen, or the screen in place."""
        import py5

        if not self._ready:
            self.setup()
        if not self.enabled:
            if source is not None:
                py5.image(source, 0, 0)
            return

        # Offscreen canvases are stored upside down relative to images, and the
        # bloom buffer is a canvas: flip its lookup when the source is an image.
        flip = 0.0 if isinstance(source, py5.Py5Graphics) else 1.0
        if source is None:
            # Snapshot the screen so the bloom and finish passes read a stable copy.
            source = py5.get_pixels(0, 0, py5.width, py5.height)
            flip = 1.0

        if self.bloom > 0:
            self._bloom_pass(source)
        set_uniforms(
            self._finish,
            bloomTex=self._ping,
            resolution=(py5.width, py5.height),
            time=py5.frame_count / 60.0,
            bloom=self.bloom,
            exposure=self.exposure,
            tonemap=self.tonemap,
            aberration=self.aberration,
            vignette=self.vignette,
            grain=self.grain,
            saturation=self.saturation,
            bloomFlipY=flip,
        )
        py5.push_style()
        py5.push_matrix()
        py5.reset_matrix()
        if py5.get_graphics().is3d():
            py5.no_lights()  # a lit scene would swap in the TEXLIGHT default shader
            py5.hint(py5.DISABLE_DEPTH_TEST)
            py5.ortho()
            py5.translate(-py5.width / 2, -py5.height / 2)
        py5.shader(self._finish)
        py5.image(source, 0, 0, py5.width, py5.height)
        py5.reset_shader()
        if py5.get_graphics().is3d():
            py5.hint(py5.ENABLE_DEPTH_TEST)
            py5.perspective()
        py5.pop_matrix()
        py5.pop_style()
