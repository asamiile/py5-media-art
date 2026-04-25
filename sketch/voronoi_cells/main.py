from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N_SEEDS = 220
BAND = 60  # rows processed per chunk

# Warm earth-tone palette (RGB 0–1)
PALETTE = np.array([
    [0.78, 0.34, 0.22],  # terracotta
    [0.89, 0.65, 0.40],  # sand
    [0.94, 0.82, 0.62],  # cream
    [0.62, 0.42, 0.28],  # rust
    [0.45, 0.58, 0.42],  # sage
    [0.72, 0.52, 0.47],  # dusty rose
    [0.82, 0.71, 0.34],  # ochre
    [0.38, 0.48, 0.62],  # slate blue
    [0.54, 0.32, 0.32],  # dark rose
    [0.25, 0.38, 0.42],  # teal
    [0.88, 0.75, 0.55],  # warm beige
    [0.42, 0.28, 0.48],  # muted purple
], dtype=np.float32)

pixels_arr = None


def compute_voronoi(width, height, seeds):
    cell_idx = np.zeros((height, width), dtype=np.int32)
    d1_map = np.zeros((height, width), dtype=np.float32)
    d2_map = np.zeros((height, width), dtype=np.float32)

    xs = np.arange(width, dtype=np.float32)

    for row_start in range(0, height, BAND):
        row_end = min(row_start + BAND, height)
        ys = np.arange(row_start, row_end, dtype=np.float32)

        Y, X = np.meshgrid(ys, xs, indexing='ij')  # (rows, cols)

        # Squared distances to all seeds: (rows, cols, N)
        dy = Y[:, :, np.newaxis] - seeds[:, 1][np.newaxis, np.newaxis, :]
        dx = X[:, :, np.newaxis] - seeds[:, 0][np.newaxis, np.newaxis, :]
        dist_sq = dx ** 2 + dy ** 2

        # Nearest cell index
        cell_idx[row_start:row_end] = np.argmin(dist_sq, axis=2)

        # Two smallest distances for edge detection
        top2 = np.partition(dist_sq, kth=1, axis=2)[:, :, :2]
        d1_map[row_start:row_end] = np.sqrt(top2[:, :, 0])
        d2_map[row_start:row_end] = np.sqrt(top2[:, :, 1])

    return cell_idx, d1_map, d2_map


def build_pixels(width, height, seeds):
    cell_idx, d1, d2 = compute_voronoi(width, height, seeds)

    # Assign palette color to each cell
    color_idx = cell_idx % len(PALETTE)
    rgb = PALETTE[color_idx]  # (H, W, 3)

    # Center-glow gradient: brighter at cell center, dims toward boundary
    max_d1 = d1.max()
    glow = np.exp(-d1 / (max_d1 * 0.18))  # exponential decay from center
    glow = glow[:, :, np.newaxis]
    rgb = np.clip(rgb * (0.3 + 0.7 * glow), 0, 1)

    # Hard dark border where d2 - d1 < threshold
    border_width = 2.2
    border = (d2 - d1) < border_width
    rgb[border] = 0.04

    # Corner vignette
    cx, cy = width / 2, height / 2
    ys, xs = np.mgrid[0:height, 0:width]
    vignette = 1 - np.clip(np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2), 0, 1) * 0.45
    rgb *= vignette[:, :, np.newaxis]

    img = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    alpha = np.full((height, width, 1), 255, dtype=np.uint8)
    return np.concatenate([alpha, img], axis=-1)


def setup():
    global pixels_arr
    py5.size(*SIZE)
    seeds = np.random.rand(N_SEEDS, 2) * np.array([SIZE[0], SIZE[1]])
    pixels_arr = build_pixels(SIZE[0], SIZE[1], seeds)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()
