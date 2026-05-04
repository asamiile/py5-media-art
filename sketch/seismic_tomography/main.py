from pathlib import Path
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

BACKGROUND = np.array([5, 8, 12], dtype=np.float32)
DEEP_BLUE = np.array([9, 31, 46], dtype=np.float32)
TEAL = np.array([20, 195, 188], dtype=np.float32)
COPPER = np.array([218, 126, 66], dtype=np.float32)
CHALK = np.array([215, 229, 216], dtype=np.float32)

velocity_grid = None
grad_x = None
grad_y = None
rng = np.random.default_rng()


def settings():
    py5.size(*SIZE)
    py5.smooth(4)


def setup():
    py5.no_loop()


def fault_center(x_norm):
    return 0.52 + 0.09 * np.sin(2.4 * np.pi * x_norm + 0.4)


def build_velocity_field(cols, rows):
    x = np.linspace(0.0, 1.0, cols)
    y = np.linspace(0.0, 1.0, rows)
    xv, yv = np.meshgrid(x, y)

    field = 0.18 * np.sin(2.0 * np.pi * (xv * 0.65 + yv * 0.15))
    field += 0.12 * np.cos(2.0 * np.pi * (yv * 1.15 - xv * 0.22))

    for _ in range(9):
        cx, cy = rng.uniform(0.05, 0.95), rng.uniform(0.08, 0.92)
        sx, sy = rng.uniform(0.055, 0.16), rng.uniform(0.045, 0.13)
        amp = rng.uniform(-0.55, 0.72)
        field += amp * np.exp(-(((xv - cx) / sx) ** 2 + ((yv - cy) / sy) ** 2))

    fault = yv - fault_center(xv)
    field += -0.9 * np.exp(-(fault / 0.025) ** 2)
    field += 0.38 * np.tanh(fault * 24.0)
    field += 0.05 * rng.normal(size=(rows, cols))
    return np.clip(field, -1.15, 1.15)


def render_background():
    rows, cols = SIZE[1], SIZE[0]
    field = build_velocity_field(cols, rows)
    ridge = np.abs(np.gradient(field, axis=1)) + np.abs(np.gradient(field, axis=0))
    ridge = np.clip(ridge * 5.0, 0.0, 1.0)

    cold = np.clip(-field, 0.0, 1.0)
    warm = np.clip(field, 0.0, 1.0)
    img = BACKGROUND[None, None, :] * np.ones((rows, cols, 3), dtype=np.float32)
    img += cold[:, :, None] * DEEP_BLUE[None, None, :] * 0.95
    img += warm[:, :, None] * COPPER[None, None, :] * 0.34
    img += ridge[:, :, None] * TEAL[None, None, :] * 0.42

    x = np.linspace(0.0, 1.0, cols)
    y = np.linspace(0.0, 1.0, rows)
    vignette = ((x[None, :] - 0.5) ** 2 / 0.34 + (y[:, None] - 0.5) ** 2 / 0.24)
    img *= np.clip(1.0 - vignette * 0.42, 0.52, 1.0)[:, :, None]
    img += rng.normal(0, 2.0, img.shape)

    rgba = np.empty((rows, cols, 4), dtype=np.uint8)
    rgba[:, :, 0] = 255
    rgba[:, :, 1:] = np.clip(img, 0, 255).astype(np.uint8)
    py5.load_np_pixels()
    retina_h, retina_w = py5.np_pixels.shape[:2]
    if (retina_h, retina_w) != (rows, cols):
        sy = max(1, retina_h // rows)
        sx = max(1, retina_w // cols)
        rgba = np.repeat(np.repeat(rgba, sy, axis=0), sx, axis=1)
    py5.np_pixels[:] = rgba[:retina_h, :retina_w]
    py5.update_np_pixels()


def prepare_ray_field():
    global velocity_grid, grad_x, grad_y
    velocity_grid = build_velocity_field(300, 170)
    gy, gx = np.gradient(velocity_grid)
    grad_x = gx
    grad_y = gy


def sample_grid(grid, x_norm, y_norm):
    h, w = grid.shape
    x = np.clip(x_norm * (w - 1), 0, w - 1.001)
    y = np.clip(y_norm * (h - 1), 0, h - 1.001)
    x0 = int(x)
    y0 = int(y)
    tx = x - x0
    ty = y - y0
    x1 = min(x0 + 1, w - 1)
    y1 = min(y0 + 1, h - 1)
    a = grid[y0, x0] * (1 - tx) + grid[y0, x1] * tx
    b = grid[y1, x0] * (1 - tx) + grid[y1, x1] * tx
    return a * (1 - ty) + b * ty


def trace_ray(start, target, steps=86):
    pos = np.array(start, dtype=np.float32)
    target = np.array(target, dtype=np.float32)
    points = [pos.copy()]
    residual = 0.0

    for _ in range(steps):
        direct = target - pos
        dist = np.linalg.norm(direct) + 1e-6
        direction = direct / dist
        gx = sample_grid(grad_x, pos[0], pos[1])
        gy = sample_grid(grad_y, pos[0], pos[1])
        bend = np.array([gx, gy], dtype=np.float32) * -0.34
        direction = direction + bend
        direction /= np.linalg.norm(direction) + 1e-6
        speed = 0.008 + min(dist, 0.025)
        pos = pos + direction * speed
        pos = np.clip(pos, 0.0, 1.0)
        points.append(pos.copy())
        residual += abs(sample_grid(velocity_grid, pos[0], pos[1])) * speed
        if dist < 0.012:
            break

    return np.array(points), residual


def draw_residual_contours():
    levels = [-0.75, -0.42, -0.12, 0.18, 0.48, 0.78]
    h, w = velocity_grid.shape
    sx = py5.width / (w - 1)
    sy = py5.height / (h - 1)
    cases = {
        1: [(0, 0.5), (0.5, 0)],
        2: [(0.5, 0), (1, 0.5)],
        3: [(0, 0.5), (1, 0.5)],
        4: [(1, 0.5), (0.5, 1)],
        5: [(0, 0.5), (0.5, 0), (1, 0.5), (0.5, 1)],
        6: [(0.5, 0), (0.5, 1)],
        7: [(0, 0.5), (0.5, 1)],
        8: [(0.5, 1), (0, 0.5)],
        9: [(0.5, 0), (0.5, 1)],
        10: [(0.5, 0), (1, 0.5), (0, 0.5), (0.5, 1)],
        11: [(1, 0.5), (0.5, 1)],
        12: [(0, 0.5), (1, 0.5)],
        13: [(0.5, 0), (1, 0.5)],
        14: [(0, 0.5), (0.5, 0)],
    }

    for level in levels:
        py5.stroke(*(TEAL if level < 0 else COPPER), 42)
        py5.stroke_weight(0.8 if abs(level) < 0.5 else 1.15)
        for y in range(h - 1):
            for x in range(w - 1):
                a = velocity_grid[y, x] > level
                b = velocity_grid[y, x + 1] > level
                c = velocity_grid[y + 1, x + 1] > level
                d = velocity_grid[y + 1, x] > level
                idx = a + 2 * b + 4 * c + 8 * d
                pts = cases.get(idx)
                if not pts:
                    continue
                for i in range(0, len(pts), 2):
                    p0 = pts[i]
                    p1 = pts[i + 1]
                    py5.line((x + p0[0]) * sx, (y + p0[1]) * sy, (x + p1[0]) * sx, (y + p1[1]) * sy)


def draw_fault_trace():
    py5.no_fill()
    for weight, alpha, color in [(22, 22, COPPER), (7, 84, COPPER), (1.4, 190, CHALK)]:
        py5.stroke(*color, alpha)
        py5.stroke_weight(weight)
        py5.begin_shape()
        for i in range(180):
            x = i / 179
            y = fault_center(x) + 0.012 * np.sin(i * 0.41)
            py5.vertex(x * py5.width, y * py5.height)
        py5.end_shape()


def draw_ray_fans():
    sources = []
    receivers = []
    for y in np.linspace(0.09, 0.91, 18):
        sources.append((0.035, y + rng.uniform(-0.012, 0.012)))
        receivers.append((0.965, y + rng.uniform(-0.012, 0.012)))
    for x in np.linspace(0.10, 0.90, 13):
        sources.append((x + rng.uniform(-0.014, 0.014), 0.955))
        receivers.append((x + rng.uniform(-0.014, 0.014), 0.045))

    pairs = []
    for i, s in enumerate(sources):
        for offset in (-7, -3, 2, 6):
            pairs.append((s, receivers[(i + offset) % len(receivers)]))
    rng.shuffle(pairs)

    for index, (start, target) in enumerate(pairs[:170]):
        points, residual = trace_ray(start, target)
        hot = min(1.0, residual * 1.8)
        color = TEAL * (1.0 - hot) + COPPER * hot
        alpha = 22 + hot * 60
        py5.stroke(*color, alpha)
        py5.stroke_weight(0.7 + hot * 1.8)
        py5.no_fill()
        py5.begin_shape()
        for p in points:
            py5.vertex(p[0] * py5.width, p[1] * py5.height)
        py5.end_shape()

        if index % 11 == 0:
            marker = points[len(points) // 2]
            py5.no_stroke()
            py5.fill(*CHALK, 42 + hot * 90)
            py5.circle(marker[0] * py5.width, marker[1] * py5.height, 2.5 + hot * 5)

    py5.no_stroke()
    for x, y in sources + receivers:
        py5.fill(*CHALK, 150)
        py5.rect(x * py5.width - 2.5, y * py5.height - 2.5, 5, 5)


def draw_grid_ticks():
    py5.stroke(145, 170, 165, 28)
    py5.stroke_weight(1)
    for x in np.linspace(0.08, 0.92, 15):
        py5.line(x * py5.width, 0, x * py5.width, py5.height)
    for y in np.linspace(0.10, 0.90, 9):
        py5.line(0, y * py5.height, py5.width, y * py5.height)


def draw():
    prepare_ray_field()
    render_background()
    draw_grid_ticks()
    draw_residual_contours()
    draw_ray_fans()
    draw_fault_trace()
    py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()
