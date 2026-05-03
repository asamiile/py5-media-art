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


def render_impact_palimpest():
    width, height = SIZE
    rng = np.random.default_rng()
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height

    terrain = (
        0.028 * np.sin(nx * 32.0 + rng.uniform(0, 6.28))
        + 0.020 * np.sin(ny * 41.0 + rng.uniform(0, 6.28))
        + 0.012 * np.sin((nx + ny) * 76.0 + rng.uniform(0, 6.28))
    )
    ejecta = np.zeros_like(terrain)
    rim_mask = np.zeros_like(terrain)
    bowl_mask = np.zeros_like(terrain)
    dust = np.zeros_like(terrain)

    craters = []
    for _ in range(42):
        r = rng.uniform(0.018, 0.105)
        cx = rng.uniform(-0.92, 0.92)
        cy = rng.uniform(-0.50, 0.50)
        depth = rng.uniform(0.035, 0.16) * (0.08 / r) ** 0.18
        craters.append((cx, cy, r, depth, rng.uniform(0, 6.28)))
    craters.sort(key=lambda c: c[2], reverse=True)

    for cx, cy, r, depth, phase in craters:
        dx = nx - cx
        dy = ny - cy
        d = np.sqrt(dx * dx + dy * dy) / r
        angle = np.arctan2(dy, dx)
        bowl = -depth * np.exp(-(d / 0.58) ** 2)
        az_light = np.cos(angle + 0.68) * 0.24 + 1.0
        rim = depth * 0.46 * az_light * np.exp(-((d - 1.0) / 0.16) ** 2)
        slump = -depth * 0.18 * np.exp(-((d - 1.34) / 0.28) ** 2)
        terrain += bowl + rim + slump
        rim_mask += np.exp(-((d - 1.0) / 0.13) ** 2) * az_light
        bowl_mask += np.exp(-(d / 0.72) ** 2) * depth

        ray_pattern = smoothstep(0.78, 0.99, np.sin(angle * rng.integers(7, 15) + phase))
        ray_decay = np.exp(-np.maximum(d - 1.0, 0.0) / rng.uniform(1.1, 2.6))
        radial_gate = smoothstep(1.0, 1.22, d) * smoothstep(4.8, 1.7, d)
        ejecta += ray_pattern * ray_decay * radial_gate * depth * rng.uniform(0.7, 1.5)
        dust += np.exp(-((d - 1.55) / 0.55) ** 2) * depth * 0.25

    gy, gx = np.gradient(terrain)
    normal_z = 1.0 / np.sqrt(gx * gx * 220.0 + gy * gy * 220.0 + 1.0)
    normal_x = -gx * 14.0 * normal_z
    normal_y = -gy * 14.0 * normal_z
    light = np.array([-0.55, -0.42, 0.72], dtype=np.float32)
    light /= np.linalg.norm(light)
    shade = np.clip(normal_x * light[0] + normal_y * light[1] + normal_z * light[2], 0.0, 1.0)
    shade = shade ** 1.35

    img = np.zeros((height, width, 3), dtype=np.float32)
    img[:] = np.array([8, 9, 11], dtype=np.float32)
    img += shade[..., None] * np.array([58, 62, 67], dtype=np.float32)
    depth_tone = smoothstep(np.percentile(bowl_mask, 54), np.percentile(bowl_mask, 98), bowl_mask)
    img *= 1.0 - depth_tone[..., None] * 0.34
    add_rgb(img, smoothstep(0.04, 0.20, ejecta), (174, 116, 72), 0.40)
    add_rgb(img, smoothstep(0.30, 1.25, rim_mask), (142, 154, 150), 0.16)
    add_rgb(img, smoothstep(0.02, 0.15, dust), (78, 106, 124), 0.36)

    shadow = smoothstep(0.42, -0.04, shade)
    add_rgb(img, shadow, (16, 24, 36), 0.62)
    add_rgb(img, depth_tone * (1.0 - shade), (7, 11, 17), 0.74)

    micro = (
        np.sin(nx * 180.0 + ny * 23.0)
        * np.sin(ny * 146.0 - nx * 31.0)
        + 0.5 * np.sin((nx + ny) * 260.0)
    )
    add_rgb(img, smoothstep(0.62, 1.0, micro), (42, 46, 48), 0.18)

    radius = np.sqrt(nx * nx + ny * ny)
    img *= (1.0 - np.clip(radius * 1.2 - 0.18, 0.0, 1.0)[..., None] * 0.38)
    img += rng.normal(0.0, 2.0, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_impact_palimpest()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()
