import struct
"""
kinetic_abelian_sandpile_mandala_2d

A 4K kinetic visualization of the Bak-Tang-Wiesenfeld Abelian Sandpile model —
a cellular automaton demonstrating self-organized criticality. Sand grains are
continuously added to the center of a grid. When any cell accumulates 4 or more
grains, it topples: distributing one grain to each of its 4 neighbors. Through
millions of cascading topplings, a breathtaking fractal mandala with exact 4-fold
symmetry crystallizes from pure local rules.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np

import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840x2160

# --- Simulation grid ---
# We run the sandpile in a square grid centered on screen.
# Grid side: odd number so center is a single cell.
# Keep grid manageable for NumPy speed: 1201x1201
GRID_SIZE = 1201
CX = GRID_SIZE // 2   # center x
CY = GRID_SIZE // 2   # center y

# Grains added per frame (controls speed of expansion)
# More grains → faster growth. We ramp up over time.
GRAINS_PER_FRAME_BASE = 2000
GRAINS_PER_FRAME_MAX = 8000

# Toppling iterations per frame (limits compute time)
MAX_TOPPLE_PASSES = 50

# 4-color palette mapped to grain counts 0..3 (ARGB int32)
# 0 → near-black deep void
# 1 → electric indigo/violet
# 2 → bioluminescent teal/cyan
# 3 → solar gold/amber
def hsb_to_argb(h, s, b, a=255):
    """Convert HSB (0-360, 0-255, 0-255) to signed int32 ARGB (py5 format)."""
    hf = (h % 360) / 360.0
    sf = s / 255.0
    bf = b / 255.0
    if sf == 0:
        r = g = bl = int(bf * 255)
    else:
        i = int(hf * 6)
        f = hf * 6 - i
        p = bf * (1 - sf)
        q = bf * (1 - f * sf)
        t = bf * (1 - (1 - f) * sf)
        i %= 6
        pairs = [(bf, t, p), (q, bf, p), (p, bf, t),
                 (p, q, bf), (t, p, bf), (bf, p, q)]
        rf, gf, blf = pairs[i]
        r, g, bl = int(rf * 255), int(gf * 255), int(blf * 255)
    # py5 pixels use signed int32; pack as uint32 then reinterpret
    val = (a << 24) | (r << 16) | (g << 8) | bl
    return struct.unpack('i', struct.pack('I', val & 0xFFFFFFFF))[0]

COLOR_MAP = np.array([
    hsb_to_argb(240, 200, 18),   # 0 grains: near-black indigo void
    hsb_to_argb(270, 240, 200),  # 1 grain:  electric violet/indigo
    hsb_to_argb(185, 255, 230),  # 2 grains: bioluminescent teal/cyan
    hsb_to_argb(45,  240, 255),  # 3 grains: solar gold/amber
], dtype=np.int32)

# Glow accent colors for border rings (ARGB)
GLOW_RING_COLOR = hsb_to_argb(185, 200, 255, 80)

# --- State ---
grid = None       # int32 array, shape (GRID_SIZE, GRID_SIZE)
total_added = 0   # total grains added so far
pimg = None       # Py5Image buffer for blit


def run_topple_passes(g, max_passes):
    """
    Fully relax the sandpile using vectorized NumPy operations.
    Returns the relaxed grid and number of topple events.
    """
    total_topplings = 0
    for _ in range(max_passes):
        unstable = g >= 4
        if not unstable.any():
            break
        # Each unstable cell loses 4 grains and gives 1 to each neighbor
        g[unstable] -= 4
        # Distribute to 4-connected neighbors (avoiding boundary issues)
        g[:-1, :] += unstable[1:, :]    # from south
        g[1:, :]  += unstable[:-1, :]   # from north
        g[:, :-1] += unstable[:, 1:]    # from east
        g[:, 1:]  += unstable[:, :-1]   # from west
        total_topplings += int(unstable.sum())
    return g, total_topplings


def render_grid_to_argb(g, W, H):
    """
    Map the sandpile grid to a 4K ARGB image array.
    The grid is centered and zoomed to fill the screen.
    """
    # Figure out which region of the grid is "interesting"
    # Find bounding box of non-zero cells (with a margin)
    nz = np.nonzero(g)
    if len(nz[0]) == 0:
        # Nothing yet — return blank
        return np.full((H, W), COLOR_MAP[0], dtype=np.int32)

    margin = 10
    r0 = max(0, nz[0].min() - margin)
    r1 = min(GRID_SIZE, nz[0].max() + margin + 1)
    c0 = max(0, nz[1].min() - margin)
    c1 = min(GRID_SIZE, nz[1].max() + margin + 1)

    # Crop the active region
    crop = g[r0:r1, c0:c1]    # shape (rh, rw)
    rh, rw = crop.shape

    # Map to color
    clamped = np.clip(crop, 0, 3)
    color_crop = COLOR_MAP[clamped]  # shape (rh, rw), int32

    # Scale to fit screen (maintain square aspect, no stretch)
    scale = min(W / rw, H / rh)
    new_w = int(rw * scale)
    new_h = int(rh * scale)

    # Nearest-neighbor upscale via index broadcasting
    row_idx = (np.arange(new_h) / scale).astype(np.int32)
    col_idx = (np.arange(new_w) / scale).astype(np.int32)
    row_idx = np.clip(row_idx, 0, rh - 1)
    col_idx = np.clip(col_idx, 0, rw - 1)
    scaled = color_crop[np.ix_(row_idx, col_idx)]  # (new_h, new_w)

    # Center on canvas
    canvas = np.full((H, W), COLOR_MAP[0], dtype=np.int32)
    y_off = (H - new_h) // 2
    x_off = (W - new_w) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = scaled

    return canvas


def setup():
    global grid, pimg

    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize grid
    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)

    # CPU-heap ARGB image buffer
    pimg = py5.create_image(py5.width, py5.height, py5.ARGB)


def draw():
    global grid, total_added

    fc = py5.frame_count
    W, H = py5.width, py5.height
    t = fc / TOTAL_FRAMES  # 0 → 1

    # --- Add grains at center ---
    # Ramp up grains over time for increasing drama
    grains_this_frame = int(
        GRAINS_PER_FRAME_BASE + (GRAINS_PER_FRAME_MAX - GRAINS_PER_FRAME_BASE) * t
    )
    grid[CY, CX] += grains_this_frame
    total_added += grains_this_frame

    # --- Topple ---
    grid, n_topplings = run_topple_passes(grid, MAX_TOPPLE_PASSES)

    # --- Render ---
    canvas = render_grid_to_argb(grid, W, H)

    # Add subtle pulsing glow ring at the expansion frontier
    # (find radius of the non-zero region and draw a circle)
    nz = np.nonzero(grid)
    if len(nz[0]) > 0:
        max_r = max(
            abs(nz[0].max() - CY),
            abs(nz[0].min() - CY),
            abs(nz[1].max() - CX),
            abs(nz[1].min() - CX),
        )
        # The screen radius of the frontier
        rh = (nz[0].max() - nz[0].min()) + 20
        rw = (nz[1].max() - nz[1].min()) + 20
        scale = min(W / max(1, rw), H / max(1, rh))
        screen_r = int(max_r * scale)
        cx_s = W // 2
        cy_s = H // 2

        # Draw glow ring using vectorized distance field
        ring_w = max(4, int(scale * 3))
        ys = np.arange(max(0, cy_s - screen_r - ring_w - 1),
                       min(H, cy_s + screen_r + ring_w + 2))
        xs = np.arange(max(0, cx_s - screen_r - ring_w - 1),
                       min(W, cx_s + screen_r + ring_w + 2))
        if len(ys) > 0 and len(xs) > 0:
            yy, xx = np.meshgrid(ys, xs, indexing='ij')
            dists = np.sqrt((xx - cx_s) ** 2 + (yy - cy_s) ** 2)
            pulse = abs(np.sin(t * np.pi * 6 + dists * 0.01))
            ring_mask = (dists >= screen_r - ring_w) & (dists <= screen_r + ring_w)
            if ring_mask.any():
                # Blend glow ring (teal/cyan additive tint)
                alpha = (pulse[ring_mask] * 80).astype(np.int64)
                base = canvas[ys[0]:ys[-1]+1, xs[0]:xs[-1]+1][ring_mask].astype(np.int64)
                # Reinterpret signed int32 as unsigned for bit extraction
                base_u = base & 0xFFFFFFFF
                br = (base_u >> 16) & 0xFF
                bg = (base_u >> 8) & 0xFF
                bb = base_u & 0xFF
                nr = br
                ng = np.clip(bg + alpha, 0, 255)
                nbl = np.clip(bb + alpha, 0, 255)
                blended_u = (0xFF << 24) | (nr << 16) | (ng << 8) | nbl
                # Convert back to signed int32
                blended_s = blended_u.astype(np.uint32).view(np.int32)
                canvas[ys[0]:ys[-1]+1, xs[0]:xs[-1]+1][ring_mask] = blended_s

    # --- Blit to Py5Image ---
    pimg.load_pixels()
    pimg.pixels[:] = canvas.flatten()
    pimg.update_pixels()

    # Draw to canvas
    py5.background(0)
    py5.image(pimg, 0, 0)

    # --- HUD overlay ---
    scale_x = W / 960
    txt_size = int(11 * scale_x)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    py5.no_stroke()

    # Dark panel
    py5.fill(0, 0, 10, 200)
    py5.rect(0, 0, int(280 * scale_x), int(80 * scale_x), 0, 0, 8, 0)

    py5.fill(185, 200, 240)
    py5.text_size(txt_size)
    py5.text("ABELIAN SANDPILE  SOC", int(10 * scale_x), int(18 * scale_x))

    py5.fill(45, 200, 220)
    py5.text_size(int(9 * scale_x))
    grains_m = total_added / 1_000_000
    py5.text(f"Grains added: {grains_m:.2f}M", int(10 * scale_x), int(38 * scale_x))
    py5.text(f"Active cells: {int((grid > 0).sum()):,}", int(10 * scale_x), int(54 * scale_x))
    py5.text(f"Max height:   {int(grid.max())}", int(10 * scale_x), int(70 * scale_x))

    # Progress bar
    py5.fill(0, 0, 20)
    py5.rect(0, H - int(5 * scale_x), W, int(5 * scale_x))
    py5.fill(185, 255, 200)
    py5.rect(0, H - int(5 * scale_x), int(W * t), int(5 * scale_x))

    # Watermark
    py5.fill(185, 60, 150, 100)
    py5.text_size(int(8 * scale_x))
    py5.text(WORK_NAME, int(10 * scale_x), H - int(10 * scale_x))

    # Fail-safe
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {fc}. Aborting.")
            import os
            os._exit(1)

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | "
              f"Grains: {total_added:,} | Active: {int((grid > 0).sum()):,}")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Preview snapshot: mid-frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames removed.")

        import os
        os._exit(0)


py5.run_sketch()
