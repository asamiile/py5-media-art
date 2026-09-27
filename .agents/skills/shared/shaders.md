# GLSL Shaders (optional)

Shaders are one tool among many, not a requirement. Choose them when the brief benefits; plain CPU/numpy sketches remain the default.

Implementation: `lib/shaders.py` + shared GLSL in `lib/glsl/`. Smoke test: `uv run python scripts/check_shaders.py`.

## When to use

| Use | For | API |
| --- | --- | --- |
| **PostFX** (finishing pass) | Light-emitting subjects (glow, neon, plasma, stars, fire), cinematic grading, film texture | `PostFX(...)` → `fx.apply()` |
| **GPU field** (fragment shader) | Per-pixel fields that are slow on CPU at 4K: domain-warped noise, interference, reaction-like patterns, raymarched SDF, caustics | `load_shader(...)` + `draw_fullscreen(...)` |

## When not to use

- The work's character is crisp vector line / flat graphic design — bloom and grain blur its identity.
- Heavy simulation state (particles, fluids, graphs) that lives in numpy: keep the simulation on CPU; PostFX may still be applied on top.
- Do not stack every effect by default. Start from the defaults (subtle) and justify each strong setting by the theme. Avoid the "generic shader demo" look the same way the Artist avoids rainbow palettes.

## Requirements

- Renderer must be OpenGL: `py5.size(*SIZE, py5.P2D)` or `py5.P3D`, plus `py5.pixel_density(1)`.
- py5 `>= 0.10.11a0` (bundles JOGL 2.6). Older py5 crashes on macOS 27 with P2D/P3D ("Must only be used from the main thread", exit 133).
- Shaders are loaded in `setup()`, after `size()`.

## PostFX

```python
from lib.shaders import PostFX

fx = PostFX(bloom=0.8, bloom_threshold=0.6, tonemap=1.0, aberration=0.002, vignette=0.3, grain=0.03)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    fx.setup()

def draw():
    py5.background(...)       # redraws every frame
    ...                       # drawing
    fx.apply()                # last, before blank check / save_frame
```

Parameters (all effects off at 0): `bloom` strength, `bloom_threshold` (0–1 luminance), `bloom_radius`, `bloom_passes`, `exposure`, `tonemap` (0–1, filmic ACES), `aberration` (radial RGB split, ~0.001–0.005), `vignette` (0–1), `grain` (~0.02–0.06), `saturation` (1 = unchanged), `enabled`.

**Accumulating sketches** (no `background()` each frame, trails that build up): `fx.apply()` in place would re-apply the effect every frame and compound it. Draw into an offscreen canvas instead:

```python
def setup():
    ...
    fx.setup()
    global canvas
    canvas = fx.create_canvas()

def draw():
    canvas.begin_draw()
    ...                       # draw with canvas.* instead of py5.*
    canvas.end_draw()
    fx.apply(canvas)          # screen = processed copy; canvas keeps the raw accumulation
```

## GPU field

Copy `lib/glsl/field_example.glsl` to `sketch/{work_name}/{work_name}.glsl` (or a descriptive `*.glsl` name) and edit it.

```python
from lib.shaders import PostFX, draw_fullscreen, load_shader

SEED = random.uniform(0, 1000)
fx = PostFX(bloom=0.6, tonemap=1.0)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    global field
    field = load_shader(SKETCH_DIR / "field.glsl")
    fx.setup()

def draw():
    draw_fullscreen(field, colorA=(0.02, 0.03, 0.1), colorB=(0.85, 0.35, 0.2), seed=SEED)
    fx.apply()
```

- `draw_fullscreen` sets `resolution` (vec2, pixels) and `time` (seconds at 60 fps) automatically; other keyword args become uniforms (tuples → vecN, bools → int, Py5Graphics/Py5Image → sampler2D).
- `#include "noise.glsl"` pulls in `snoise(vec3)` and `fbm(vec3, octaves)` from `lib/glsl/`; includes also resolve against the sketch folder.
- **No fixed seeds**: pass a random `seed` (e.g. `random.uniform(0, 1000)`) as a uniform and offset the noise domain with it, so each run differs.
- Use `time` for animation so the video frame rate stays in control; do not rely on wall-clock time.
- Colors in GLSL are 0–1 floats.

## Gotchas

- A py5 error during a shader sketch leaves the window open instead of exiting. Run previews with a timeout and treat a hang as a failure.
- `create_graphics(..., P2D)` must go through one `begin_draw()`/`end_draw()` before loading a shader into it (`PostFX` and `create_canvas()` already do).
- In P3D, `fx.apply()` turns lights off and disables depth test for the finishing quad; call `py5.lights()` again at the start of the next frame (normal practice).
- Offscreen canvases are stored upside down relative to images; `PostFX` compensates. If you sample a Py5Graphics yourself in GLSL, flip `y` when mixing it with an image source.
- Shader compile errors show up as `RuntimeError: cannot load shader file ...` with the GLSL log; fix the GLSL rather than falling back silently.
- Verify the effect visually in the saved preview: bloom halos must sit on the bright shapes, and grain must look like noise (no grid pattern).
