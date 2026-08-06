"""
kinetic_verlet_cloth_membrane_2d
A vast silk cloth billowing and tearing in an unseen storm —
the tension between structure and surrender.

Technique: Vectorized NumPy Verlet integration cloth simulation with
structural/shear constraints and dynamic tearing propagation.
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# --- Cloth parameters ---
COLS = 60
ROWS = 45
ITERATIONS = 12       # constraint solver iterations
GRAVITY = 0.55        # strong gravity
DAMPING = 0.995
TEAR_DIST = 2.6       # tear when constraint stretched beyond this × rest_len
WIND_BASE = 1.2       # strong base wind
WIND_TURB = 0.8       # turbulence amplitude

# Global state (NumPy arrays for performance)
pos_x = None   # shape (ROWS, COLS)
pos_y = None
prev_x = None
prev_y = None
pinned = None  # bool mask
rest_h = None  # horizontal rest lengths
rest_v = None  # vertical rest lengths
rest_d1 = None # diagonal rest lengths (top-left → bottom-right)
rest_d2 = None # diagonal rest lengths (top-right → bottom-left)
torn_h = None  # bool: horizontal constraint torn
torn_v = None
torn_d1 = None
torn_d2 = None
cell_spacing = None
preview_saved = False


def build_cloth():
    global pos_x, pos_y, prev_x, prev_y, pinned
    global rest_h, rest_v, rest_d1, rest_d2
    global torn_h, torn_v, torn_d1, torn_d2, cell_spacing
    W, H = SIZE

    cloth_left = W * 0.07
    cloth_right = W * 0.93
    cloth_top = H * 0.05
    cloth_bottom = H * 0.92

    xs = np.linspace(cloth_left, cloth_right, COLS)
    ys = np.linspace(cloth_top, cloth_bottom, ROWS)
    gx, gy = np.meshgrid(xs, ys)

    pos_x = gx.copy()
    pos_y = gy.copy()
    prev_x = gx.copy()
    prev_y = gy.copy()

    # Pin top row — every 6th node
    pinned = np.zeros((ROWS, COLS), dtype=bool)
    for c in range(0, COLS, 6):
        pinned[0, c] = True

    # Rest lengths from initial positions
    cell_spacing = (cloth_right - cloth_left) / (COLS - 1)
    rest_h = np.sqrt(np.diff(pos_x, axis=1)**2 + np.diff(pos_y, axis=1)**2)  # (ROWS, COLS-1)
    rest_v = np.sqrt(np.diff(pos_x, axis=0)**2 + np.diff(pos_y, axis=0)**2)  # (ROWS-1, COLS)
    dx_d1 = pos_x[1:, 1:] - pos_x[:-1, :-1]
    dy_d1 = pos_y[1:, 1:] - pos_y[:-1, :-1]
    rest_d1 = np.sqrt(dx_d1**2 + dy_d1**2)
    dx_d2 = pos_x[1:, :-1] - pos_x[:-1, 1:]
    dy_d2 = pos_y[1:, :-1] - pos_y[:-1, 1:]
    rest_d2 = np.sqrt(dx_d2**2 + dy_d2**2)

    torn_h = np.zeros_like(rest_h, dtype=bool)
    torn_v = np.zeros_like(rest_v, dtype=bool)
    torn_d1 = np.zeros_like(rest_d1, dtype=bool)
    torn_d2 = np.zeros_like(rest_d2, dtype=bool)

    print(f"[Setup] Cloth {COLS}×{ROWS}, {COLS*ROWS} nodes, pinned: {pinned.sum()}")


def update_cloth(frame):
    global pos_x, pos_y, prev_x, prev_y
    global torn_h, torn_v, torn_d1, torn_d2
    t = frame / FPS

    # Wind: strong sinusoidal gusts + per-row depth variation
    wind_gust = WIND_BASE * np.sin(t * 0.9 + 0.3) * (0.5 + 0.5 * np.cos(t * 2.1))
    wind_burst = WIND_TURB * np.sin(t * 3.7) * np.cos(t * 1.1)
    wind_total = wind_gust + wind_burst

    # Row-varying wind (more wind at bottom — like cloth catching air)
    row_factor = np.linspace(0.4, 1.0, ROWS)[:, np.newaxis]

    # Verlet integration
    vx = (pos_x - prev_x) * DAMPING
    vy = (pos_y - prev_y) * DAMPING

    new_x = pos_x + vx + wind_total * row_factor
    new_y = pos_y + vy + GRAVITY

    # Apply: don't update pinned nodes
    mask = ~pinned
    prev_x = np.where(mask, pos_x, prev_x)
    prev_y = np.where(mask, pos_y, prev_y)
    pos_x = np.where(mask, new_x, pos_x)
    pos_y = np.where(mask, new_y, pos_y)

    # Constraint solver iterations
    for _ in range(ITERATIONS):
        _solve_horizontal()
        _solve_vertical()
        _solve_diagonal1()
        _solve_diagonal2()

    # Check tearing (periodic — every 3 frames)
    if frame % 3 == 0:
        _check_tears()


def _solve_horizontal():
    """Solve horizontal structural constraints."""
    n1x = pos_x[:, :-1]
    n1y = pos_y[:, :-1]
    n2x = pos_x[:, 1:]
    n2y = pos_y[:, 1:]
    dx = n2x - n1x
    dy = n2y - n1y
    dist = np.sqrt(dx**2 + dy**2)
    dist = np.maximum(dist, 1e-8)
    diff = (dist - rest_h) / dist * 0.5
    diff = np.where(torn_h, 0.0, diff)
    mx = dx * diff
    my = dy * diff
    # Move n1 right
    not_pinned_l = ~pinned[:, :-1]
    not_pinned_r = ~pinned[:, 1:]
    pos_x[:, :-1] += np.where(not_pinned_l, mx, 0.0)
    pos_y[:, :-1] += np.where(not_pinned_l, my, 0.0)
    pos_x[:, 1:] -= np.where(not_pinned_r, mx, 0.0)
    pos_y[:, 1:] -= np.where(not_pinned_r, my, 0.0)


def _solve_vertical():
    """Solve vertical structural constraints."""
    n1x = pos_x[:-1, :]
    n1y = pos_y[:-1, :]
    n2x = pos_x[1:, :]
    n2y = pos_y[1:, :]
    dx = n2x - n1x
    dy = n2y - n1y
    dist = np.sqrt(dx**2 + dy**2)
    dist = np.maximum(dist, 1e-8)
    diff = (dist - rest_v) / dist * 0.5
    diff = np.where(torn_v, 0.0, diff)
    mx = dx * diff
    my = dy * diff
    not_pinned_t = ~pinned[:-1, :]
    not_pinned_b = ~pinned[1:, :]
    pos_x[:-1, :] += np.where(not_pinned_t, mx, 0.0)
    pos_y[:-1, :] += np.where(not_pinned_t, my, 0.0)
    pos_x[1:, :] -= np.where(not_pinned_b, mx, 0.0)
    pos_y[1:, :] -= np.where(not_pinned_b, my, 0.0)


def _solve_diagonal1():
    n1x = pos_x[:-1, :-1]
    n1y = pos_y[:-1, :-1]
    n2x = pos_x[1:, 1:]
    n2y = pos_y[1:, 1:]
    dx = n2x - n1x
    dy = n2y - n1y
    dist = np.sqrt(dx**2 + dy**2)
    dist = np.maximum(dist, 1e-8)
    diff = (dist - rest_d1) / dist * 0.5
    diff = np.where(torn_d1, 0.0, diff)
    mx = dx * diff
    my = dy * diff
    not_pin1 = ~pinned[:-1, :-1]
    not_pin2 = ~pinned[1:, 1:]
    pos_x[:-1, :-1] += np.where(not_pin1, mx, 0.0)
    pos_y[:-1, :-1] += np.where(not_pin1, my, 0.0)
    pos_x[1:, 1:] -= np.where(not_pin2, mx, 0.0)
    pos_y[1:, 1:] -= np.where(not_pin2, my, 0.0)


def _solve_diagonal2():
    n1x = pos_x[:-1, 1:]
    n1y = pos_y[:-1, 1:]
    n2x = pos_x[1:, :-1]
    n2y = pos_y[1:, :-1]
    dx = n2x - n1x
    dy = n2y - n1y
    dist = np.sqrt(dx**2 + dy**2)
    dist = np.maximum(dist, 1e-8)
    diff = (dist - rest_d2) / dist * 0.5
    diff = np.where(torn_d2, 0.0, diff)
    mx = dx * diff
    my = dy * diff
    not_pin1 = ~pinned[:-1, 1:]
    not_pin2 = ~pinned[1:, :-1]
    pos_x[:-1, 1:] += np.where(not_pin1, mx, 0.0)
    pos_y[:-1, 1:] += np.where(not_pin1, my, 0.0)
    pos_x[1:, :-1] -= np.where(not_pin2, mx, 0.0)
    pos_y[1:, :-1] -= np.where(not_pin2, my, 0.0)


def _check_tears():
    global torn_h, torn_v, torn_d1, torn_d2
    # Horizontal
    dx = pos_x[:, 1:] - pos_x[:, :-1]
    dy = pos_y[:, 1:] - pos_y[:, :-1]
    dist_h = np.sqrt(dx**2 + dy**2)
    torn_h = torn_h | (dist_h > rest_h * TEAR_DIST)
    # Vertical
    dx = pos_x[1:, :] - pos_x[:-1, :]
    dy = pos_y[1:, :] - pos_y[:-1, :]
    dist_v = np.sqrt(dx**2 + dy**2)
    torn_v = torn_v | (dist_v > rest_v * TEAR_DIST)
    # Diagonals
    dx = pos_x[1:, 1:] - pos_x[:-1, :-1]
    dy = pos_y[1:, 1:] - pos_y[:-1, :-1]
    torn_d1 = torn_d1 | (np.sqrt(dx**2 + dy**2) > rest_d1 * TEAR_DIST)
    dx = pos_x[1:, :-1] - pos_x[:-1, 1:]
    dy = pos_y[1:, :-1] - pos_y[:-1, 1:]
    torn_d2 = torn_d2 | (np.sqrt(dx**2 + dy**2) > rest_d2 * TEAR_DIST)


def draw_cloth(frame):
    W, H = SIZE
    t = frame / TOTAL_FRAMES

    # Compute per-quad strain for coloring
    # Horizontal strain field
    dx_h = pos_x[:, 1:] - pos_x[:, :-1]
    dy_h = pos_y[:, 1:] - pos_y[:, :-1]
    strain_h = np.sqrt(dx_h**2 + dy_h**2) / (rest_h + 1e-8) - 1.0  # (ROWS, COLS-1)

    # Draw quads (filled mesh faces)
    for row in range(ROWS - 1):
        for col in range(COLS - 1):
            # Skip quad if any surrounding constraint is torn (creates holes)
            h_top_torn = torn_h[row, col]
            h_bot_torn = torn_h[row+1, col]
            v_left_torn = torn_v[row, col]
            v_right_torn = torn_v[row, col+1]
            if h_top_torn and h_bot_torn and v_left_torn and v_right_torn:
                continue

            x00, y00 = pos_x[row, col], pos_y[row, col]
            x10, y10 = pos_x[row, col+1], pos_y[row, col+1]
            x01, y01 = pos_x[row+1, col], pos_y[row+1, col]
            x11, y11 = pos_x[row+1, col+1], pos_y[row+1, col+1]

            # Strain coloring: ivory → amber → crimson at high strain
            s = float(np.clip(strain_h[row, col] * 4.0, 0.0, 1.0))
            depth = row / (ROWS - 1)

            # Fold lighting: use diagonal ratio — symmetric, no checkerboard
            # d1: top-left → bottom-right, d2: top-right → bottom-left
            d1 = np.sqrt((x11 - x00)**2 + (y11 - y00)**2)
            d2 = np.sqrt((x10 - x01)**2 + (y10 - y01)**2)
            dmax = max(d1, d2, 1e-8)
            fold = abs(d1 - d2) / dmax  # 0 = flat quad, 1 = heavily folded/skewed
            # Cross product z-component: positive = facing light, negative = shadowed
            cx_ = (x10 - x00) * (y01 - y00) - (y10 - y00) * (x01 - x00)
            face_light = 0.5 + 0.5 * np.tanh(cx_ / (dmax * dmax + 1e-8))
            light = 0.55 + 0.30 * face_light + 0.15 * (1.0 - fold)

            # Color: ivory silk base, strained areas amber-red
            r = int(np.clip((222 - 42*s) * light * (1.0 - 0.12*depth), 0, 255))
            g = int(np.clip((205 - 85*s) * light * (1.0 - 0.18*depth), 0, 255))
            b = int(np.clip((178 - 135*s) * light * (1.0 - 0.22*depth), 0, 255))

            py5.no_stroke()
            py5.fill(r, g, b, 235)
            py5.begin_shape()
            py5.vertex(x00, y00)
            py5.vertex(x10, y10)
            py5.vertex(x11, y11)
            py5.vertex(x01, y01)
            py5.end_shape(py5.CLOSE)

    # Draw horizontal grid lines (cloth weave)
    py5.stroke_weight(0.8)
    for row in range(ROWS):
        for col in range(COLS - 1):
            if torn_h[row, col]:
                # Draw torn edge with crimson glow
                py5.stroke(190, 45, 25, 180)
                py5.stroke_weight(2.0)
            else:
                py5.stroke(240, 225, 200, 50)
                py5.stroke_weight(0.7)
            py5.line(pos_x[row, col], pos_y[row, col],
                     pos_x[row, col+1], pos_y[row, col+1])

    # Draw vertical grid lines
    for row in range(ROWS - 1):
        for col in range(COLS):
            if torn_v[row, col]:
                py5.stroke(190, 45, 25, 180)
                py5.stroke_weight(2.0)
            else:
                py5.stroke(240, 225, 200, 50)
                py5.stroke_weight(0.7)
            py5.line(pos_x[row, col], pos_y[row, col],
                     pos_x[row+1, col], pos_y[row+1, col])

    # Draw pin markers
    py5.no_stroke()
    for c in range(COLS):
        if pinned[0, c]:
            py5.fill(255, 240, 200, 230)
            py5.circle(pos_x[0, c], pos_y[0, c], 10)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    py5.background(18, 16, 24)
    FRAMES_DIR.mkdir(exist_ok=True)
    build_cloth()


def draw():
    global preview_saved
    W, H = SIZE
    frame = py5.frame_count

    # Clear with full opaque background
    py5.background(18, 16, 24)

    # Subtle vignette
    py5.no_stroke()
    for i in range(12):
        alpha = int(8 + i * 5)
        margin = i * 30
        py5.fill(8, 6, 14, alpha)
        py5.rect(0, 0, W, margin)
        py5.rect(0, H - margin, W, margin)
        py5.rect(0, 0, margin, H)
        py5.rect(W - margin, 0, margin, H)

    # Update simulation
    update_cloth(frame)

    # Draw cloth
    draw_cloth(frame)

    # Telemetry: torn constraint count
    total_torn = int(torn_h.sum() + torn_v.sum())
    py5.fill(180, 160, 130, 160)
    py5.text_size(22)
    py5.text(f"tears: {total_torn}", 40, H - 40)

    # Blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)

    # Progress
    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    # Save preview at midpoint directly from py5
    if frame == TOTAL_FRAMES // 2 and not preview_saved:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        preview_saved = True
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    # Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)


py5.run_sketch()
