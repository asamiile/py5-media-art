from pathlib import Path
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename, save_preview_pil
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def add_rgb(img, mask, color, gain=1.0):
    img += np.clip(mask, 0.0, 1.0)[..., None] * np.array(color, dtype=np.float32) * gain


def render_crease_memory():
    width, height = SIZE
    rng = np.random.default_rng()

    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height
    radius = np.sqrt(nx * nx + ny * ny)

    heightfield = np.zeros((height, width), dtype=np.float32)
    stress = np.zeros_like(heightfield)
    ridge = np.zeros_like(heightfield)
    crease_family = np.zeros_like(heightfield)

    crease_count = rng.integers(16, 23)
    base_angles = rng.choice(
        np.array([-0.92, -0.48, -0.18, 0.22, 0.56, 0.94], dtype=np.float32),
        size=crease_count,
        replace=True,
    )

    for i, angle in enumerate(base_angles):
        angle += rng.normal(0.0, 0.07)
        ca, sa = np.cos(angle), np.sin(angle)
        offset = rng.uniform(-0.64, 0.64)
        distance = nx * ca + ny * sa - offset
        sharpness = rng.uniform(0.008, 0.026)
        amplitude = rng.uniform(-0.15, 0.18)

        local_fold = np.tanh(distance / sharpness)
        heightfield += amplitude * local_fold

        line = np.exp(-(distance / (sharpness * rng.uniform(1.1, 2.2))) ** 2)
        stress += line * abs(amplitude) * rng.uniform(0.9, 1.7)
        ridge += np.exp(-(distance / (sharpness * 0.55)) ** 2) * rng.uniform(0.25, 1.0)

        if i % 3 == 0:
            crease_family += line * rng.uniform(0.3, 0.8)
        else:
            crease_family -= line * rng.uniform(0.15, 0.5)

    # A few short secondary creases stop the surface from becoming too mechanically parallel.
    for _ in range(18):
        angle = rng.uniform(-np.pi, np.pi)
        ca, sa = np.cos(angle), np.sin(angle)
        cx = rng.uniform(-0.72, 0.72)
        cy = rng.uniform(-0.36, 0.36)
        along = (nx - cx) * -sa + (ny - cy) * ca
        across = (nx - cx) * ca + (ny - cy) * sa
        length_mask = smoothstep(0.34, 0.0, np.abs(along))
        sharpness = rng.uniform(0.006, 0.018)
        amp = rng.uniform(-0.055, 0.075)
        local = np.tanh(across / sharpness) * length_mask
        heightfield += amp * local
        short_line = np.exp(-(across / sharpness) ** 2) * length_mask
        stress += short_line * abs(amp) * 2.4
        ridge += short_line * 0.65

    wave_grain = (
        0.018 * np.sin(nx * 44.0 + ny * 13.0 + rng.uniform(0, 6.28))
        + 0.014 * np.sin(nx * -23.0 + ny * 39.0 + rng.uniform(0, 6.28))
        + 0.008 * np.cos((nx - ny) * 81.0 + rng.uniform(0, 6.28))
    )
    heightfield += wave_grain

    gy, gx = np.gradient(heightfield)
    normal_z = 1.0 / np.sqrt(gx * gx * 180.0 + gy * gy * 180.0 + 1.0)
    normal_x = -gx * 13.0 * normal_z
    normal_y = -gy * 13.0 * normal_z
    light = np.array([-0.42, -0.56, 0.72], dtype=np.float32)
    light /= np.linalg.norm(light)
    shade = np.clip(normal_x * light[0] + normal_y * light[1] + normal_z * light[2], 0.0, 1.0)
    shade = shade ** 1.45

    img = np.zeros((height, width, 3), dtype=np.float32)
    img[:] = np.array([7, 8, 10], dtype=np.float32)
    base = 0.18 + 0.82 * shade
    img += base[..., None] * np.array([24, 27, 33], dtype=np.float32)

    cold_side = smoothstep(-0.035, 0.22, heightfield)
    warm_side = smoothstep(0.18, -0.08, heightfield)
    add_rgb(img, cold_side * 0.45, (38, 136, 145), 0.84)
    add_rgb(img, warm_side * 0.32, (132, 82, 118), 0.76)

    fine_stress = smoothstep(np.percentile(stress, 72), np.percentile(stress, 98.6), stress)
    hot_ridge = smoothstep(np.percentile(ridge, 82), np.percentile(ridge, 99.4), ridge)
    incision = smoothstep(np.percentile(ridge, 94), np.percentile(ridge, 99.75), ridge)
    crease_shadow = smoothstep(np.percentile(ridge, 74), np.percentile(ridge, 92), ridge) * (1.0 - incision)
    img *= (1.0 - crease_shadow[..., None] * 0.18)
    add_rgb(img, fine_stress, (210, 158, 88), 0.48)
    add_rgb(img, hot_ridge * (0.45 + 0.55 * np.clip(crease_family, 0, 1)), (70, 220, 206), 0.58)
    add_rgb(img, incision, (218, 255, 230), 0.72)

    facet = np.abs(np.sin(heightfield * 38.0 + nx * 9.0 - ny * 6.0))
    facet_lines = smoothstep(0.92, 0.995, facet) * smoothstep(np.percentile(stress, 45), np.percentile(stress, 88), stress)
    add_rgb(img, facet_lines, (28, 76, 82), 0.38)

    shadow = smoothstep(0.18, 0.92, radius)
    img *= (1.0 - shadow[..., None] * 0.34)
    img += rng.normal(0.0, 2.0, img.shape).astype(np.float32)
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_crease_memory()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()
