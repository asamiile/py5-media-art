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

BG = np.array([7, 9, 12], dtype=np.float32)
PEAT = np.array([33, 47, 39], dtype=np.float32)
MOSS = np.array([82, 130, 96], dtype=np.float32)
AMBER = np.array([214, 151, 69], dtype=np.float32)
VIOLET = np.array([126, 91, 155], dtype=np.float32)
CHALK = np.array([225, 224, 199], dtype=np.float32)

rng = np.random.default_rng()


def settings():
    py5.size(*SIZE)
    py5.smooth(4)


def setup():
    py5.no_loop()


def blend(a, b, t):
    return a * (1.0 - t) + b * t


def draw_pixel_field():
    cols, rows = SIZE
    x = np.linspace(0.0, 1.0, cols)
    y = np.linspace(0.0, 1.0, rows)
    xv, yv = np.meshgrid(x, y)

    field = 0.34 * np.sin(2.0 * np.pi * (xv * 1.7 + yv * 0.18))
    field += 0.22 * np.cos(2.0 * np.pi * (yv * 2.4 - xv * 0.35))
    field += 0.16 * np.sin(2.0 * np.pi * (xv * 4.2 + yv * 1.4))

    for _ in range(16):
        cx, cy = rng.uniform(-0.05, 1.05), rng.uniform(-0.02, 1.02)
        sx, sy = rng.uniform(0.035, 0.18), rng.uniform(0.025, 0.10)
        amp = rng.uniform(-0.45, 0.55)
        field += amp * np.exp(-(((xv - cx) / sx) ** 2 + ((yv - cy) / sy) ** 2))

    field = np.clip(field, -1.0, 1.0)
    warm = np.clip(field, 0.0, 1.0)
    cool = np.clip(-field, 0.0, 1.0)
    bands = 0.5 + 0.5 * np.sin((yv * 44.0 + 0.9 * np.sin(xv * 11.0)) * np.pi)
    img = BG[None, None, :] * np.ones((rows, cols, 3), dtype=np.float32)
    img += cool[:, :, None] * PEAT[None, None, :] * 1.1
    img += warm[:, :, None] * MOSS[None, None, :] * 0.58
    img += (bands[:, :, None] ** 8) * VIOLET[None, None, :] * 0.12
    img += rng.normal(0, 2.2, img.shape)

    vignette = ((xv - 0.5) ** 2 / 0.33 + (yv - 0.5) ** 2 / 0.28)
    img *= np.clip(1.0 - vignette * 0.5, 0.45, 1.0)[:, :, None]

    pixels = np.empty((rows, cols, 4), dtype=np.uint8)
    pixels[:, :, 0] = 255
    pixels[:, :, 1:] = np.clip(img, 0, 255).astype(np.uint8)
    py5.load_np_pixels()
    retina_h, retina_w = py5.np_pixels.shape[:2]
    if (retina_h, retina_w) != (rows, cols):
        sy = max(1, retina_h // rows)
        sx = max(1, retina_w // cols)
        pixels = np.repeat(np.repeat(pixels, sy, axis=0), sx, axis=1)
    py5.np_pixels[:] = pixels[:retina_h, :retina_w]
    py5.update_np_pixels()


def niche_for_generation(generation, generations):
    t = generation / max(1, generations - 1)
    x = 0.14 + 0.75 * t
    body = 0.62 - 0.34 * t + 0.08 * np.sin(t * np.pi * 3.0)
    tone = 0.18 + 0.68 * t
    speed = 0.74 - 0.42 * np.sin(t * np.pi * 0.74) ** 2
    return np.array([x, body, tone, speed])


def evaluate(population, generation, generations):
    target = niche_for_generation(generation, generations)
    dx = np.abs(population[:, 0] - target[0])
    body = np.abs(population[:, 1] - target[1])
    tone = np.abs(population[:, 2] - target[2])
    speed = np.abs(population[:, 3] - target[3])
    camouflage = np.exp(-(dx * 4.4 + body * 2.2 + tone * 3.0 + speed * 1.4))
    diversity_bonus = 0.12 * np.sin(population[:, 0] * np.pi * 7.0 + generation * 0.38) ** 2
    return camouflage + diversity_bonus + rng.uniform(0.0, 0.035, len(population))


def simulate_evolution(generations=52, population_size=86, elite_count=18):
    population = rng.random((population_size, 4))
    parent_slots = np.arange(population_size)
    records = []
    links = []

    for generation in range(generations):
        fitness = evaluate(population, generation, generations)
        order = np.argsort(fitness)[::-1]
        survivors = order[:elite_count]

        row_y = 0.07 + 0.86 * generation / max(1, generations - 1)
        for rank, idx in enumerate(order[:38]):
            gene = population[idx].copy()
            x = 0.06 + 0.88 * gene[0]
            y = row_y + rng.normal(0.0, 0.004)
            records.append(
                {
                    "generation": generation,
                    "rank": rank,
                    "x": x,
                    "y": y,
                    "body": gene[1],
                    "tone": gene[2],
                    "speed": gene[3],
                    "fitness": fitness[idx],
                    "slot": parent_slots[idx],
                }
            )

        weights = fitness[survivors] ** 2.4
        weights = weights / weights.sum()
        parents = rng.choice(survivors, size=population_size, replace=True, p=weights)
        children = population[parents].copy()
        mutation = rng.normal(0.0, [0.055, 0.06, 0.05, 0.045], children.shape)
        mutation_mask = rng.random(children.shape) < [0.55, 0.48, 0.52, 0.42]
        children = np.clip(children + mutation * mutation_mask, 0.0, 1.0)

        if generation > 0:
            for child_index, parent_index in enumerate(parents[:42]):
                links.append((parent_slots[parent_index], child_index, generation - 1, generation))

        parent_slots = np.arange(population_size)
        population = children

    return records, links


def record_lookup(records):
    lookup = {}
    for record in records:
        key = (record["generation"], record["slot"])
        if key not in lookup or record["rank"] < lookup[key]["rank"]:
            lookup[key] = record
    return lookup


def draw_selection_pressure():
    records, links = simulate_evolution()
    lookup = record_lookup(records)

    py5.blend_mode(py5.ADD)
    for _ in range(850):
        x = rng.uniform(0.06, 0.94) * py5.width
        y = rng.uniform(0.07, 0.93) * py5.height
        scale = rng.uniform(1.6, 7.5)
        tone = rng.uniform(0.0, 1.0)
        color = blend(VIOLET, MOSS, tone)
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(rng.uniform(-1.1, 1.1))
        py5.no_stroke()
        py5.fill(*color, rng.uniform(3, 13))
        py5.ellipse(0, 0, scale * rng.uniform(2.0, 4.6), scale)
        py5.pop_matrix()

    py5.blend_mode(py5.ADD)
    for parent_slot, child_slot, g0, g1 in links:
        a = lookup.get((g0, parent_slot))
        b = lookup.get((g1, child_slot))
        if not a or not b:
            continue
        strength = min(1.0, (a["fitness"] + b["fitness"]) * 0.52)
        color = blend(VIOLET, AMBER, b["tone"])
        py5.stroke(*color, 10 + strength * 26)
        py5.stroke_weight(0.45 + strength * 1.05)
        py5.line(a["x"] * py5.width, a["y"] * py5.height, b["x"] * py5.width, b["y"] * py5.height)

    py5.blend_mode(py5.BLEND)
    for generation in range(0, 52, 4):
        y = (0.07 + 0.86 * generation / 51) * py5.height
        target = niche_for_generation(generation, 52)
        x = (0.06 + 0.88 * target[0]) * py5.width
        py5.stroke(*CHALK, 24)
        py5.stroke_weight(1)
        py5.line(0, y, py5.width, y)
        py5.no_stroke()
        py5.fill(*AMBER, 44)
        py5.circle(x, y, 18 + 26 * target[1])

    for record in sorted(records, key=lambda r: r["fitness"]):
        fitness = min(1.0, record["fitness"] * 1.55)
        body = 4.0 + 19.0 * record["body"]
        wing = 3.0 + 22.0 * record["speed"]
        color = blend(MOSS, AMBER, record["tone"])
        if record["rank"] < 5:
            color = blend(color, CHALK, 0.36)
        alpha = 34 + fitness * 165
        x = record["x"] * py5.width
        y = record["y"] * py5.height

        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate((record["tone"] - 0.5) * 1.8 + np.sin(record["generation"] * 0.35) * 0.18)
        py5.no_stroke()
        py5.fill(*color, alpha * 0.28)
        py5.ellipse(0, 0, body * 3.2, wing * 1.5)
        py5.fill(*color, alpha)
        py5.ellipse(0, 0, body * 1.65, body * 0.78)
        py5.stroke(*CHALK, alpha * 0.52)
        py5.stroke_weight(0.65 + fitness * 1.2)
        py5.line(-body * 0.8, 0, body * 0.8, 0)
        if record["rank"] < 8:
            py5.no_fill()
            py5.stroke(*AMBER, 64 + fitness * 80)
            py5.stroke_weight(0.8)
            py5.circle(0, 0, body * 2.5)
        py5.pop_matrix()

    py5.no_fill()
    py5.stroke(*CHALK, 72)
    py5.stroke_weight(1.2)
    py5.rect(py5.width * 0.045, py5.height * 0.055, py5.width * 0.91, py5.height * 0.89)


def draw():
    draw_pixel_field()
    draw_selection_pressure()
    py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()
