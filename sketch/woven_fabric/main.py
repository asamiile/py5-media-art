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

# Theme: "Mathematical loom" — a Jacquard-style woven textile where a sinusoidal
# function acts as the weave matrix: at each warp × weft intersection, a sine-cosine
# product determines which thread lies on top, producing flowing organic cloth patterns.

THREAD_W = 10    # thread width in pixels
THREAD_G =  2    # gap between threads (shadow/space)
PERIOD   = THREAD_W + THREAD_G   # = 12 px per thread

# Palette: warm sienna warp, cool indigo weft, near-black gaps
BG_COL   = np.array([ 10,   8,  14], dtype=np.uint8)
WARP_COL = np.array([188,  90,  40], dtype=np.float32)   # warm sienna (vertical)
WEFT_COL = np.array([ 45,  68, 155], dtype=np.float32)   # cool indigo (horizontal)
DARK_F   = 0.60   # shadow darkening factor at thread edges


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    x = np.arange(W, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    gx, gy = np.meshgrid(x, y)    # (H, W)

    j = (gx / PERIOD).astype(np.int32)   # warp thread index
    i = (gy / PERIOD).astype(np.int32)   # weft thread index
    xw = (gx % PERIOD).astype(np.int32)  # position within warp period
    yw = (gy % PERIOD).astype(np.int32)  # position within weft period

    on_warp = xw < THREAD_W    # pixel lies on a vertical warp thread
    on_weft = yw < THREAD_W    # pixel lies on a horizontal weft thread

    # Weave matrix: sinusoidal combination creates flowing organic cloth pattern
    fi = i.astype(np.float32)
    fj = j.astype(np.float32)
    weave_val = (np.sin(fi * 0.42) * np.cos(fj * 0.35)
                 + 0.55 * np.sin(fi * 0.17 + fj * 0.28))
    weft_on_top = weave_val > 0   # True → weft thread over warp at this intersection

    # ---- Assign base colours ----
    r_ch = np.full((H, W), BG_COL[0], dtype=np.float32)
    g_ch = np.full((H, W), BG_COL[1], dtype=np.float32)
    b_ch = np.full((H, W), BG_COL[2], dtype=np.float32)

    warp_only = on_warp & ~on_weft
    weft_only = on_weft & ~on_warp
    isect     = on_warp & on_weft

    r_ch[warp_only] = WARP_COL[0]
    g_ch[warp_only] = WARP_COL[1]
    b_ch[warp_only] = WARP_COL[2]

    r_ch[weft_only] = WEFT_COL[0]
    g_ch[weft_only] = WEFT_COL[1]
    b_ch[weft_only] = WEFT_COL[2]

    # Intersection: show the top-thread colour
    weft_top = isect & weft_on_top
    warp_top = isect & ~weft_on_top

    r_ch[weft_top] = WEFT_COL[0]
    g_ch[weft_top] = WEFT_COL[1]
    b_ch[weft_top] = WEFT_COL[2]

    r_ch[warp_top] = WARP_COL[0]
    g_ch[warp_top] = WARP_COL[1]
    b_ch[warp_top] = WARP_COL[2]

    # ---- Shadow at thread edges for 3-D roundness ----
    EDGE = 1   # shadow width in pixels

    # Warp thread: darken left/right edges
    warp_edge = on_warp & ((xw < EDGE) | (xw >= THREAD_W - EDGE))
    r_ch[warp_edge] *= DARK_F
    g_ch[warp_edge] *= DARK_F
    b_ch[warp_edge] *= DARK_F

    # Weft thread: darken top/bottom edges (but NOT where warp is on top at intersection)
    weft_edge = on_weft & ~warp_top & ((yw < EDGE) | (yw >= THREAD_W - EDGE))
    r_ch[weft_edge] *= DARK_F
    g_ch[weft_edge] *= DARK_F
    b_ch[weft_edge] *= DARK_F

    # Underthread at intersection: slightly dim (thread is under, partially shadowed)
    r_ch[warp_top] *= 0.88   # warp on top at intersection → weft is under (N/A here)
    # Note: the pixel already shows the top thread color; no additional dim needed

    r_ch = np.clip(r_ch, 0, 255).astype(np.uint8)
    g_ch = np.clip(g_ch, 0, 255).astype(np.uint8)
    b_ch = np.clip(b_ch, 0, 255).astype(np.uint8)

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
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()
