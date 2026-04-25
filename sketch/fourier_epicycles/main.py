from pathlib import Path
import subprocess
from collections import deque
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 6
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 360

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
SIZE = PREVIEW_SIZE

CX = SIZE[0] // 2
CY = SIZE[1] // 2

# Theme: "Clockwork orrery" — single mechanism, brass aesthetic
# One chain: trail gold→dark brown; circles dark bronze; arms dark brass; rivets at joints
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
BG_COL      = (7,   8,  14)     # #07080e near-black
RING_COL    = (42,  32,  16)    # #2a2010 very dark bronze
ARM_COL     = (138, 106, 48)    # #8a6a30 dark brass
RIVET_COL   = (162, 128,  60)   # slightly brighter brass for joints
GOLD_NEW    = np.array([232, 200, 112])  # #e8c870 recent trail
GOLD_OLD    = np.array([ 58,  48,  32])  # #3a3020 old trail → background

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

    # Draw trail — gold (recent) → dark brown (old)
    pts = list(trail)
    n = len(pts)
    if n >= 2:
        # age 0 = oldest → GOLD_OLD; age 1 = newest → GOLD_NEW
        ages = np.linspace(0.0, 1.0, n, dtype=np.float32)
        rs = (GOLD_OLD[0] * (1 - ages) + GOLD_NEW[0] * ages).astype(int)
        gs = (GOLD_OLD[1] * (1 - ages) + GOLD_NEW[1] * ages).astype(int)
        bs = (GOLD_OLD[2] * (1 - ages) + GOLD_NEW[2] * ages).astype(int)
        alphas = (40 + ages * 215).astype(int)

        py5.no_fill()
        py5.stroke_weight(2.2)
        for i in range(1, n):
            py5.stroke(rs[i], gs[i], bs[i], alphas[i])
            py5.line(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1])

    # Gold tip dot
    py5.no_stroke()
    py5.fill(*GOLD_NEW, 255)
    py5.ellipse(x0, y0, 9.0, 9.0)
    py5.fill(*GOLD_NEW, 60)
    py5.ellipse(x0, y0, 24.0, 24.0)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        last = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES:04d}.png")
        subprocess.run(["cp", last, str(SKETCH_DIR / "preview.png")], check=True)


py5.run_sketch()
