from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

N_SEEDS = 180
BAND = 60  # rows per chunk

# Theme: "Shattered glass, still" — borders are the subject
# near-black background, dark navy cells, cold steel border, ice accent
BG_COL      = np.array([8,   8,  14], dtype=np.float32) / 255.0   # #08080e
CELL_COL    = np.array([18, 26,  34], dtype=np.float32) / 255.0   # #121a22 very dark navy
BORDER_COL  = np.array([61, 96, 112], dtype=np.float32) / 255.0   # #3d6070 cold steel blue
ACCENT_COL  = np.array([168, 200, 216], dtype=np.float32) / 255.0 # #a8c8d8 pale ice blue

pixels_arr = None


def compute_voronoi(width, height, seeds):
    cell_idx = np.zeros((height, width), dtype=np.int32)
    d1_map = np.zeros((height, width), dtype=np.float32)
    d2_map = np.zeros((height, width), dtype=np.float32)
    xs = np.arange(width, dtype=np.float32)

    for row_start in range(0, height, BAND):
        row_end = min(row_start + BAND, height)
        ys = np.arange(row_start, row_end, dtype=np.float32)
        Y, X = np.meshgrid(ys, xs, indexing='ij')
        dy = Y[:, :, np.newaxis] - seeds[:, 1][np.newaxis, np.newaxis, :]
        dx = X[:, :, np.newaxis] - seeds[:, 0][np.newaxis, np.newaxis, :]
        dist_sq = dx ** 2 + dy ** 2
        cell_idx[row_start:row_end] = np.argmin(dist_sq, axis=2)
        top2 = np.partition(dist_sq, kth=1, axis=2)[:, :, :2]
        d1_map[row_start:row_end] = np.sqrt(top2[:, :, 0])
        d2_map[row_start:row_end] = np.sqrt(top2[:, :, 1])

    return cell_idx, d1_map, d2_map


def compute_delaunay_edges(seeds):
    from scipy.spatial import Delaunay
    tri = Delaunay(seeds)
    edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            a, b = simplex[i], simplex[(i + 1) % 3]
            edges.add((min(a, b), max(a, b)))
    return list(edges)


def build_pixels(width, height, seeds, accent_cells):
    cell_idx, d1, d2 = compute_voronoi(width, height, seeds)

    # All cells start as near-black
    rgb = np.tile(CELL_COL, (height, width, 1)).copy()

    # Border: where d2 - d1 < threshold → cold steel blue border
    border_w = 2.0
    border = (d2 - d1) < border_w

    # Accent: 2–3 cells get ice-blue borders instead
    accent_border = border & np.isin(cell_idx, accent_cells)
    normal_border = border & ~np.isin(cell_idx, accent_cells)

    rgb[normal_border] = BORDER_COL
    rgb[accent_border] = ACCENT_COL

    img = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    alpha = np.full((height, width, 1), 255, dtype=np.uint8)
    return np.concatenate([alpha, img], axis=-1)


def setup():
    global pixels_arr
    py5.size(*SIZE)
    seeds = np.random.rand(N_SEEDS, 2) * np.array([SIZE[0], SIZE[1]])

    # Pick 2–3 random cells for accent color
    accent_cells = np.random.choice(N_SEEDS, size=3, replace=False)
    pixels_arr = build_pixels(SIZE[0], SIZE[1], seeds, accent_cells)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()
