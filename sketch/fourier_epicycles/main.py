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

N_CHAINS = 6

# 2× scale vs original; primary amp 370 < 540 (half-height) so no canvas clipping
EPICYCLES = [
    ( 1,  370,  0.00),
    (-2,  196,  0.31),
    ( 3,  146,  0.72),
    (-4,  110,  1.10),
    ( 5,   84,  0.05),
    (-6,   62,  0.53),
    ( 7,   46,  0.98),
    (-8,   34,  0.24),
    ( 9,   26,  0.81),
    (-10,  20,  0.47),
    ( 11,  16,  0.93),
    (-12,  12,  0.17),
    ( 13,  10,  0.62),
    (-14,   8,  1.35),
    ( 15,   6,  0.29),
]

# 6 chains evenly spread around the curve so it fills in from the start
CHAIN_PHASES = np.linspace(0, 2 * np.pi, N_CHAINS, endpoint=False)
# Base hue per chain (blue → violet → magenta → orange → lime → teal)
CHAIN_HUES = (np.array([200, 260, 320, 20, 80, 140], dtype=float))

trails = [deque(maxlen=TOTAL_FRAMES) for _ in range(N_CHAINS)]


def _tip(t_val):
    x, y = float(CX), float(CY)
    for freq, amp, phase in EPICYCLES:
        x += amp * np.cos(freq * t_val + phase)
        y += amp * np.sin(freq * t_val + phase)
    return x, y


def _hsv_batch(hues_deg, s=0.92, v=1.0):
    h = hues_deg / 60.0
    ii = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p = np.full_like(hues_deg, v * (1 - s))
    q = v * (1 - s * f)
    tv = v * (1 - s * (1 - f))
    vv = np.full_like(hues_deg, v)
    cnd = [ii == k for k in range(6)]
    r = (np.select(cnd, [vv, q, p, p, tv, vv]) * 255).astype(int)
    g = (np.select(cnd, [tv, vv, vv, q, p, p]) * 255).astype(int)
    b = (np.select(cnd, [p, p, tv, vv, vv, q]) * 255).astype(int)
    return r, g, b


def _hsv_single(h_deg, s=0.92, v=1.0):
    h = h_deg / 60.0
    ii = int(h) % 6
    f = h - int(h)
    p = v * (1 - s)
    q = v * (1 - s * f)
    tv = v * (1 - s * (1 - f))
    lut = [(v, tv, p), (q, v, p), (p, v, tv), (p, q, v), (tv, p, v), (v, p, q)]
    return tuple(int(c * 255) for c in lut[ii])


def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(4, 4, 14)


def draw():
    base_t = (py5.frame_count - 1) / TOTAL_FRAMES * 2 * np.pi
    py5.background(4, 4, 14)

    # Ghost epicycle arms for chain 0 only
    x0, y0 = float(CX), float(CY)
    t0 = base_t + CHAIN_PHASES[0]
    for freq, amp, phase in EPICYCLES:
        angle = freq * t0 + phase
        nx, ny = x0 + amp * np.cos(angle), y0 + amp * np.sin(angle)
        py5.no_fill()
        py5.stroke(90, 110, 180, 10)
        py5.stroke_weight(0.5)
        py5.ellipse(x0, y0, amp * 2, amp * 2)
        py5.stroke(130, 155, 235, 28)
        py5.stroke_weight(0.7)
        py5.line(x0, y0, nx, ny)
        x0, y0 = nx, ny

    # Compute tips and update trails
    tips = []
    for ci in range(N_CHAINS):
        tx, ty = _tip(base_t + CHAIN_PHASES[ci])
        tips.append((tx, ty))
        trails[ci].append((tx, ty))

    # Draw trails
    for ci in range(N_CHAINS):
        pts = list(trails[ci])
        n = len(pts)
        if n < 2:
            continue

        ages = np.arange(n, dtype=np.float32) / max(n - 1, 1)
        hues = (CHAIN_HUES[ci] + ages * 55.0) % 360.0
        alphas = (35 + ages * 210).astype(int)
        rs, gs, bs = _hsv_batch(hues)

        # Glow pass
        py5.stroke_weight(4.5)
        for i in range(1, n):
            ga = max(int(alphas[i]) - 155, 0)
            py5.stroke(int(rs[i]), int(gs[i]), int(bs[i]), ga)
            py5.line(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1])

        # Core pass
        py5.stroke_weight(2.0)
        for i in range(1, n):
            py5.stroke(int(rs[i]), int(gs[i]), int(bs[i]), int(alphas[i]))
            py5.line(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1])

    # Tip dots
    py5.no_stroke()
    for ci, (tx, ty) in enumerate(tips):
        r, g, b = _hsv_single(CHAIN_HUES[ci])
        py5.fill(r, g, b, 235)
        py5.ellipse(tx, ty, 8, 8)
        py5.fill(r, g, b, 55)
        py5.ellipse(tx, ty, 22, 22)

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
