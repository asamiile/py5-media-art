from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Ghost geometry" — two families of concentric rings from offset centers;
# their geometric intersection traces moiré ovals — large patterns that exist nowhere
# in either ring family alone, emerging purely from layered regularity.

# Ring parameters
RING_SPACING = 20    # px between rings
RING_WIDTH   = 2.8   # px ring thickness
CENTER_OFFSET = 280  # px each center is offset from canvas center (horizontally)

# Palette: deep background, muted ring colors, bright overlap (moiré)
BG_COL      = np.array([ 7,   5,  13], dtype=np.uint8)   # near-black violet
COL_RING1   = np.array([145,  28,  28], dtype=np.float32) # dark crimson
COL_RING2   = np.array([ 28,  28, 145], dtype=np.float32) # dark navy
COL_OVERLAP = np.array([242, 228, 255], dtype=np.float32) # bright lavender-white


def setup():
    py5.size(*SIZE)
    W, H = SIZE
    cx, cy = W / 2.0, H / 2.0

    x = np.arange(W, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    gx, gy = np.meshgrid(x, y)   # (H, W)

    # Ring family A: centered at (cx - offset, cy)
    dist_a = np.sqrt((gx - (cx - CENTER_OFFSET)) ** 2 + (gy - cy) ** 2)
    g1 = (dist_a % RING_SPACING) < RING_WIDTH

    # Ring family B: centered at (cx + offset, cy)
    dist_b = np.sqrt((gx - (cx + CENTER_OFFSET)) ** 2 + (gy - cy) ** 2)
    g2 = (dist_b % RING_SPACING) < RING_WIDTH

    # Combined state: 0=bg, 1=ring A only, 2=ring B only, 3=overlap (moiré)
    state = g1.astype(np.uint8) + g2.astype(np.uint8) * 2

    # Color mapping
    r_ch = np.where(state == 3, COL_OVERLAP[0],
           np.where(state == 1, COL_RING1[0],
           np.where(state == 2, COL_RING2[0], BG_COL[0]))).astype(np.uint8)
    g_ch = np.where(state == 3, COL_OVERLAP[1],
           np.where(state == 1, COL_RING1[1],
           np.where(state == 2, COL_RING2[1], BG_COL[1]))).astype(np.uint8)
    b_ch = np.where(state == 3, COL_OVERLAP[2],
           np.where(state == 1, COL_RING1[2],
           np.where(state == 2, COL_RING2[2], BG_COL[2]))).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != H or w_buf != W:
        r_ch = np.repeat(np.repeat(r_ch, 2, axis=0), 2, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, 2, axis=0), 2, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, 2, axis=0), 2, axis=1)

    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 2] = g_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 3] = b_ch[:h_buf, :w_buf]
    py5.update_np_pixels()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()
