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
DURATION_SEC = 25
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 × 2160

CANVAS_W, CANVAS_H = SIZE

# Sandpile lives on a square grid.
# 540×540 upscaled 4× = 2160×2160, centred in 3840×2160 with 840px black bars.
GRID_SIZE = 540
GRID_SCALE = 4                    # 540 * 4 = 2160 = CANVAS_H
X_OFFSET = (CANVAS_W - GRID_SIZE * GRID_SCALE) // 2  # 840 px left/right padding

# Grains added per frame at the centre of the grid.
# 190 grains × 1500 frames = 285 000 total grains → radius ≈ 301 px < 270?
# We drop conservatively: 160 grains × 1500 = 240 000 → r ≈ 276 px.
# The sandpile still slightly overflows top/bottom (270 px), creating a
# beautiful boundary effect with grains escaping into the sink.
GRAINS_PER_FRAME = 175

# Colour palette (values 0–3).  High contrast for maximum fractal clarity.
PALETTE = np.array([
    [  8,   5,  18],   # 0 grain  — near-black midnight
    [ 12,  80, 155],   # 1 grain  — deep ocean blue
    [190, 135,  10],   # 2 grains — warm amber gold
    [235, 228, 210],   # 3 grains — bleached ivory
], dtype=np.uint8)

grid = None
pixel_buf = None


# ---------------------------------------------------------------------------
# Vectorised parallel toppling (Abelian sandpile with absorbing boundaries)
# ---------------------------------------------------------------------------

def topple():
    """Topple all unstable cells (>= 4 grains) simultaneously until stable."""
    global grid
    while True:
        unstable = grid >= 4
        if not unstable.any():
            break
        # Remove 4 grains from every unstable cell
        grid -= 4 * unstable.astype(np.int32)
        # Distribute 1 grain to each in-bounds neighbour
        # Grains that would leave the grid boundary are silently dropped (sink).
        grid[1:, :]  += unstable[:-1, :]   # down  ← from row above
        grid[:-1, :] += unstable[1:, :]    # up    ← from row below
        grid[:, 1:]  += unstable[:, :-1]   # right ← from col to left
        grid[:, :-1] += unstable[:, 1:]    # left  ← from col to right


def grid_to_rgb(g):
    """Map sandpile state (values 0–3) to an RGB image at grid resolution."""
    clamped = np.clip(g, 0, 3).astype(np.uint8)
    return PALETTE[clamped]           # (GRID_SIZE, GRID_SIZE, 3)


def setup():
    global grid, pixel_buf
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
    pixel_buf = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.uint8)
    pixel_buf[:, :, 0] = 255  # alpha channel always 255


def draw():
    global grid, pixel_buf

    frame = py5.frame_count

    # Drop grains at centre, then topple to stability
    cy, cx = GRID_SIZE // 2, GRID_SIZE // 2
    grid[cy, cx] += GRAINS_PER_FRAME
    topple()

    # Build colour image
    rgb_sm = grid_to_rgb(grid)                              # (540, 540, 3)
    rgb_lg = np.repeat(                                     # (2160, 2160, 3)
        np.repeat(rgb_sm, GRID_SCALE, axis=0),
        GRID_SCALE, axis=1
    )

    # Write into centred region of the 4K canvas
    pixel_buf[:, X_OFFSET:X_OFFSET + GRID_SIZE * GRID_SCALE, 1] = rgb_lg[:, :, 0]
    pixel_buf[:, X_OFFSET:X_OFFSET + GRID_SIZE * GRID_SCALE, 2] = rgb_lg[:, :, 1]
    pixel_buf[:, X_OFFSET:X_OFFSET + GRID_SIZE * GRID_SCALE, 3] = rgb_lg[:, :, 2]

    py5.load_np_pixels()
    py5.np_pixels[:] = pixel_buf
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame == 30 or frame % 120 == 0:
        if pixel_buf[:, :, 1:].std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} "
              f"({frame / TOTAL_FRAMES * 100:.1f}%)")

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Encoding {TOTAL_FRAMES} frames → {WORK_NAME}.mp4 ...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid_frame = TOTAL_FRAMES // 2
        shutil.copyfile(
            FRAMES_DIR / f"frame-{mid_frame:04d}.png",
            SKETCH_DIR / PREVIEW_FILENAME,
        )

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Frames directory removed.")

        import os
        os._exit(0)


py5.run_sketch()
