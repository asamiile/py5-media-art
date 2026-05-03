from pathlib import Path
import sys
from collections import deque
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, render_video_and_preview, save_animation_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = frames_dir(SKETCH_DIR)
DURATION_SEC = 6
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 360

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

CX = SIZE[0] // 2
CY = SIZE[1] // 2

# Theme: "Iridescent Cosmos" — spectral harmonics and celestial orbits
# Vibrant multi-color trail with a shifting iridescent palette
EPICYCLES = [
    ( 1,  360,  0.00),
    (-2,  190,  0.31),
    ( 3,  142,  0.72),
    (-4,  106,  1.10),
    ( 5,   80,  0.05),
    (-6,   60,  0.53),
    ( 7,   44,  0.98),
    (-8,   32,  0.24),
    ( 9,   24,  0.81),
    (-10,  18,  0.47),
    ( 11,  14,  0.93),
    (-12,  10,  0.17),
    ( 13,   8,  0.62),
    (-14,   6,  1.35),
    ( 15,   4,  0.29),
]

# Colors
BG_COL      = (5,   5,  12)     # #05050c deep space black
RING_COL    = (30,  30,  60)    # #1e1e3c dark nebula blue
ARM_COL     = (60,  60, 120)    # #3c3c78 muted cosmic blue
RIVET_COL   = (100, 100, 200)   # #6464c8 faint star light

# Iridescent Palette for the trail
PALETTE = [
    np.array([120, 40, 200]),  # Deep Purple
    np.array([40, 100, 255]),  # Electric Blue
    np.array([0, 255, 220]),   # Cyan/Teal
    np.array([255, 50, 150]),  # Hot Magenta
    np.array([255, 220, 50]),  # Solar Gold
]

trail = deque(maxlen=TOTAL_FRAMES)


def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(*BG_COL)


def draw():
    t = (py5.frame_count - 1) / TOTAL_FRAMES * 2 * np.pi
    py5.background(*BG_COL)

    # Draw epicycle rings and arms with brass rivets at each joint
    x0, y0 = float(CX), float(CY)
    py5.no_fill()
    joints = [(x0, y0)]  # track all joint positions for rivets

    for freq, amp, phase in EPICYCLES:
        angle = freq * t + phase
        nx = x0 + amp * np.cos(angle)
        ny = y0 + amp * np.sin(angle)

        # Orbit ring — very dark bronze, barely visible
        py5.stroke(*RING_COL, 80)
        py5.stroke_weight(0.8)
        py5.ellipse(x0, y0, amp * 2, amp * 2)

        # Arm — dark brass
        py5.stroke(*ARM_COL, 140)
        py5.stroke_weight(1.4)
        py5.line(x0, y0, nx, ny)

        joints.append((nx, ny))
        x0, y0 = nx, ny

    # Brass rivet dots at each joint
    py5.no_stroke()
    for jx, jy in joints[:-1]:   # all except tip (tip gets gold dot)
        py5.fill(*RIVET_COL, 200)
        py5.ellipse(jx, jy, 5.0, 5.0)

    # Update trail
    trail.append((x0, y0))

    # Draw trail — Iridescent Spectrum
    pts = list(trail)
    n = len(pts)
    if n >= 2:
        # age 0 = oldest; age 1 = newest
        ages = np.linspace(0.0, 1.0, n, dtype=np.float32)

        # Multi-stop interpolation for the trail colors
        trail_colors = np.zeros((n, 3), dtype=np.int32)
        num_stops = len(PALETTE)
        for i in range(num_stops - 1):
            mask = (ages >= i / (num_stops - 1)) & (ages <= (i + 1) / (num_stops - 1))
            if not np.any(mask):
                continue
            t_local = (ages[mask] - i / (num_stops - 1)) * (num_stops - 1)
            c0 = PALETTE[i]
            c1 = PALETTE[i+1]
            trail_colors[mask] = (c0[None, :] * (1 - t_local[:, None]) + c1[None, :] * t_local[:, None]).astype(int)

        alphas = (30 + ages * 225).astype(int)

        py5.no_fill()
        for i in range(1, n):
            # Glow effect
            py5.stroke(trail_colors[i][0], trail_colors[i][1], trail_colors[i][2], alphas[i] // 4)
            py5.stroke_weight(7.0)
            py5.line(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1])

            # Core trail
            py5.stroke(trail_colors[i][0], trail_colors[i][1], trail_colors[i][2], alphas[i])
            py5.stroke_weight(2.4)
            py5.line(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1])

    # Tip dot - matches the latest color in the palette
    tip_col = PALETTE[-1]
    py5.no_stroke()
    py5.fill(*tip_col, 255)
    py5.ellipse(x0, y0, 9.0, 9.0)
    py5.fill(*tip_col, 60)
    py5.ellipse(x0, y0, 28.0, 28.0)

    save_animation_frame(FRAMES_DIR)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_frame=TOTAL_FRAMES,
            preview_filename="preview_p1.png",
        )


py5.run_sketch()
