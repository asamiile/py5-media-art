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

# Theme: "Abstract Quantum Cells"
# Deep Amethyst background, glowing Teal boundaries, and Molten Gold accents
BG_COL      = np.array([12,  8,  20], dtype=np.float32) / 255.0   # #0c0814 Deep Amethyst
CELL_COL    = np.array([30, 15,  50], dtype=np.float32) / 255.0   # #1e0f32 Darker Purple
BORDER_COL  = np.array([0, 180, 210], dtype=np.float32) / 255.0   # #00b4d2 Luminous Teal
ACCENT_COL  = np.array([255, 190,  0], dtype=np.float32) / 255.0   # #ffbe00 Molten Gold

pixels_arr = None

def compute_voronoi(width, height, seeds):
    cell_idx = np.zeros((height, width), dtype=np.int32)
    d1_map = np.zeros((height, width), dtype=np.float32)
    d2_map = np.zeros((height, width), dtype=np.float32)
    xs = np.arange(width, dtype=np.float32)

    # Noise parameters for space warping
    warp_scale = 0.003
    warp_strength = 45.0

    for row_start in range(0, height, BAND):
        row_end = min(row_start + BAND, height)
        ys = np.arange(row_start, row_end, dtype=np.float32)
        Y, X = np.meshgrid(ys, xs, indexing='ij')
        
        # Add space warp (abstraction)
        # We use a vectorized noise-like perturbation (sine-summation for speed in numpy)
        warp_x = np.sin(Y * warp_scale * 1.5) * np.cos(X * warp_scale) * warp_strength
        warp_y = np.cos(Y * warp_scale) * np.sin(X * warp_scale * 1.2) * warp_strength
        
        X_warped = X + warp_x
        Y_warped = Y + warp_y
        
        dy = Y_warped[:, :, np.newaxis] - seeds[:, 1][np.newaxis, np.newaxis, :]
        dx = X_warped[:, :, np.newaxis] - seeds[:, 0][np.newaxis, np.newaxis, :]
        dist_sq = dx ** 2 + dy ** 2
        
        cell_idx[row_start:row_end] = np.argmin(dist_sq, axis=2)
        top2 = np.partition(dist_sq, kth=1, axis=2)[:, :, :2]
        d1_map[row_start:row_end] = np.sqrt(top2[:, :, 0])
        d2_map[row_start:row_end] = np.sqrt(top2[:, :, 1])

    return cell_idx, d1_map, d2_map


def build_pixels(width, height, seeds, accent_cells):
    cell_idx, d1, d2 = compute_voronoi(width, height, seeds)

    # Base background
    rgb = np.tile(BG_COL, (height, width, 1)).copy()
    
    # Cell color variation
    for i in range(len(seeds)):
        mask = cell_idx == i
        if i in accent_cells:
            # Gold cells (slightly glowing)
            rgb[mask] = CELL_COL * 0.5 + ACCENT_COL * 0.2
        else:
            # Amethyst cells
            rgb[mask] = CELL_COL * (0.8 + 0.4 * np.random.rand())

    # Border: Soft glow instead of hard line
    # (d2 - d1) is the distance to the second-nearest site. 
    # Small value means we are near a boundary.
    diff = d2 - d1
    
    # Glow parameters
    glow_width = 4.0
    glow = np.exp(- (diff**2) / (2 * glow_width**2))
    
    # Apply glowing borders
    is_accent = np.isin(cell_idx, accent_cells)
    
    # Vectorized color blending
    # Teal for normal, Gold for accent
    border_rgb = np.zeros_like(rgb)
    border_rgb[~is_accent] = BORDER_COL
    border_rgb[is_accent] = ACCENT_COL
    
    # Additive-like blend for the glow
    rgb = rgb * (1.0 - glow[:, :, np.newaxis] * 0.6) + border_rgb * glow[:, :, np.newaxis]

    img = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    alpha = np.full((height, width, 1), 255, dtype=np.uint8)
    return np.concatenate([alpha, img], axis=-1)


def setup():
    global pixels_arr
    py5.size(*SIZE)
    seeds = np.random.rand(N_SEEDS, 2) * np.array([SIZE[0], SIZE[1]])

    # Pick 5-8 random cells for accent color (Gold)
    accent_cells = np.random.choice(N_SEEDS, size=8, replace=False)
    pixels_arr = build_pixels(SIZE[0], SIZE[1], seeds, accent_cells)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="voronoi_cells_v2_p1.png")


py5.run_sketch()

