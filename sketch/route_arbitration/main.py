from collections import deque
from pathlib import Path
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

GRID_W = 64
GRID_H = 36
OBSTACLES = None
ROUTES = []


def find_path(start, goal, blocked):
    q = deque([start])
    parent = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and not blocked[ny, nx] and (nx, ny) not in parent:
                parent[(nx, ny)] = (x, y)
                q.append((nx, ny))
    if goal not in parent:
        return []
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]


def setup():
    global OBSTACLES, ROUTES
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.smooth(8)
    py5.no_loop()
    rng = np.random.default_rng()

    OBSTACLES = np.zeros((GRID_H, GRID_W), dtype=bool)
    for _ in range(18):
        w = rng.integers(3, 9)
        h = rng.integers(2, 6)
        x = rng.integers(2, GRID_W - w - 2)
        y = rng.integers(2, GRID_H - h - 2)
        OBSTACLES[y:y + h, x:x + w] = True

    free = np.argwhere(~OBSTACLES)
    ROUTES = []
    for _ in range(44):
        s_idx, g_idx = rng.choice(len(free), size=2, replace=False)
        sy, sx = free[s_idx]
        gy, gx = free[g_idx]
        if abs(sx - gx) + abs(sy - gy) < 24:
            continue
        path = find_path((int(sx), int(sy)), (int(gx), int(gy)), OBSTACLES)
        if len(path) > 18:
            ROUTES.append(path)


def cell_xy(cell):
    w, h = SIZE
    margin = 58
    cw = (w - margin * 2) / GRID_W
    ch = (h - margin * 2) / GRID_H
    x, y = cell
    return margin + (x + 0.5) * cw, margin + (y + 0.5) * ch


def draw():
    w, h = SIZE
    py5.background(7, 9, 12)
    py5.blend_mode(py5.SCREEN)

    margin = 58
    cw = (w - margin * 2) / GRID_W
    ch = (h - margin * 2) / GRID_H

    py5.stroke(42, 52, 60, 42)
    py5.stroke_weight(0.55)
    for gx in range(GRID_W + 1):
        x = margin + gx * cw
        py5.line(x, margin, x, h - margin)
    for gy in range(GRID_H + 1):
        y = margin + gy * ch
        py5.line(margin, y, w - margin, y)

    py5.no_stroke()
    for y in range(GRID_H):
        for x in range(GRID_W):
            if OBSTACLES[y, x]:
                px = margin + x * cw
                py = margin + y * ch
                py5.fill(20, 23, 26, 225)
                py5.rect(px, py, cw * 0.98, ch * 0.98)
                py5.fill(62, 68, 70, 42)
                py5.rect(px + 2, py + 2, cw * 0.98 - 4, 3)

    heat = {}
    for path in ROUTES:
        for cell in path:
            heat[cell] = heat.get(cell, 0) + 1

    for path_i, path in enumerate(ROUTES):
        color = (76, 142, 178) if path_i % 3 else (75, 210, 132)
        py5.no_fill()
        py5.stroke(*color, 42)
        py5.stroke_weight(2.0)
        py5.begin_shape()
        for cell in path:
            x, y = cell_xy(cell)
            py5.vertex(x, y)
        py5.end_shape()

        if path_i % 2 == 0:
            for k, cell in enumerate(path[::5]):
                x, y = cell_xy(cell)
                py5.stroke(224, 238, 230, 62)
                py5.stroke_weight(1.0)
                py5.line(x - 5, y - 5, x + 5, y + 5)

    for (x, y), count in heat.items():
        if count < 3:
            continue
        px, py = cell_xy((x, y))
        py5.no_stroke()
        py5.fill(226, 156, 70, min(38 + count * 18, 180))
        py5.circle(px, py, min(6 + count * 2.8, 24))
        if count > 5:
            py5.fill(242, 238, 190, 96)
            py5.circle(px, py, 4)

    # Edge priority markers.
    py5.no_fill()
    py5.stroke(238, 244, 232, 68)
    py5.stroke_weight(1.1)
    for path in ROUTES[:18]:
        for cell in (path[0], path[-1]):
            x, y = cell_xy(cell)
            py5.rect(x - 7, y - 7, 14, 14)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


if __name__ == "__main__":
    py5.run_sketch()
