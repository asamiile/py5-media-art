from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Printed interference" — wave superposition rendered as halftone dots
# Two interleaved dot grids (offset by half a cell) encode complementary fields:
# Grid A (navy) = wave amplitude; Grid B (sienna) = inverse amplitude
# Dot radius proportional to field value; empty cells show cream background

PITCH      = 22         # grid cell size in logical pixels
WAVELENGTH = 160.0      # wave spatial period in pixels
N_SOURCES  = 4          # wave point sources

BG_COL  = (248, 244, 234)  # warm cream paper
COL_A   = ( 24,  38,  72)  # deep navy (dominant interference)
COL_B   = (162,  88,  40)  # warm burnt sienna (complementary)


def compute_field(gx, gy, sources, wavelength):
    """Sum cosine waves from each source, normalize to [0, 1]."""
    field = np.zeros(gx.shape, dtype=np.float32)
    for sx, sy in sources:
        d = np.sqrt((gx - sx) ** 2 + (gy - sy) ** 2)
        field += np.cos(2.0 * np.pi * d / wavelength)
    mn, mx = field.min(), field.max()
    return (field - mn) / (mx - mn + 1e-8)


def draw_dots(field, radii_max, col):
    radii = field * radii_max
    ny, nx = field.shape
    py5.fill(*col)
    py5.no_stroke()
    for j in range(ny):
        for i in range(nx):
            r = float(radii[j, i])
            if r > 0.4:
                py5.ellipse(float(gxA[j, i] if col == COL_A else gxB[j, i]),
                            float(gyA[j, i] if col == COL_A else gyB[j, i]),
                            r * 2, r * 2)


# Pre-compute grids at module level so draw_dots can reference them
W, H = SIZE
_pitch = PITCH
_ox_a, _oy_a = 0, 0
_ox_b, _oy_b = PITCH // 2, PITCH // 2

_xs_a = np.arange(_ox_a, W + _pitch, _pitch)
_ys_a = np.arange(_oy_a, H + _pitch, _pitch)
gxA, gyA = np.meshgrid(_xs_a, _ys_a)

_xs_b = np.arange(_ox_b, W + _pitch, _pitch)
_ys_b = np.arange(_oy_b, H + _pitch, _pitch)
gxB, gyB = np.meshgrid(_xs_b, _ys_b)


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)
    py5.no_stroke()

    rng = np.random.default_rng()
    # Sources placed inside the canvas (not at edges)
    sources = rng.integers([W // 6, H // 6], [5 * W // 6, 5 * H // 6],
                           size=(N_SOURCES, 2))

    # Grid A: navy dots — wave amplitude (power-stretched for dramatic size range)
    fieldA = compute_field(gxA, gyA, sources, WAVELENGTH)
    fieldA = fieldA ** 1.8  # push small dots smaller, large dots larger
    fieldA = (fieldA - fieldA.min()) / (fieldA.max() - fieldA.min() + 1e-8)
    radii_max = PITCH * 0.50
    py5.fill(*COL_A)
    for j in range(gxA.shape[0]):
        for i in range(gxA.shape[1]):
            r = float(fieldA[j, i]) * radii_max
            if r > 0.5:
                py5.ellipse(float(gxA[j, i]), float(gyA[j, i]), r * 2, r * 2)

    # Grid B: sienna dots — complementary (inverse) amplitude
    fieldB = compute_field(gxB, gyB, sources, WAVELENGTH)
    fieldB = 1.0 - fieldB  # invert
    fieldB = fieldB ** 1.8
    fieldB = (fieldB - fieldB.min()) / (fieldB.max() - fieldB.min() + 1e-8)
    py5.fill(*COL_B)
    for j in range(gxB.shape[0]):
        for i in range(gxB.shape[1]):
            r = float(fieldB[j, i]) * radii_max
            if r > 0.5:
                py5.ellipse(float(gxB[j, i]), float(gyB[j, i]), r * 2, r * 2)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()
