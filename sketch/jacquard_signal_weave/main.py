from __future__ import annotations

from pathlib import Path
import math
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

BG = (10, 11, 13)
THREAD_DARK = (26, 29, 31)
THREAD = (152, 164, 142)
CYAN = (68, 209, 199)
MULBERRY = (178, 82, 126)
AMBER = (232, 166, 70)
INDIGO = (79, 108, 185)
PAPER = (188, 170, 124)

rng = np.random.default_rng()
WARP_COUNT = 96
WEFT_COUNT = 54
CARD_COLS = 32
CARD_ROWS = 9
warp_phase = rng.uniform(0.0, math.tau, WARP_COUNT)
weft_phase = rng.uniform(0.0, math.tau, WEFT_COUNT)
card_pattern = rng.random((CARD_ROWS, CARD_COLS)) > 0.63
lint = rng.uniform(0.0, 1.0, (320, 4))


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def draw_thread(draw: ImageDraw.ImageDraw, pts, color, alpha, width) -> None:
    for scale, a in ((5, alpha * 0.08), (2, alpha * 0.22), (1, alpha)):
        draw.line(pts, fill=rgba(color, a), width=max(1, int(width * scale)))


def render_frame(frame_no: int, frame_path: Path) -> None:
    w, h = PREVIEW_SIZE
    t = frame_no / TOTAL_FRAMES * DURATION_SEC
    loom_phase = (frame_no / TOTAL_FRAMES * 2.0) % 1.0

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(40):
        y0 = int(i / 40 * h)
        y1 = int((i + 1) / 40 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (22, 26, 27), i / 39), 225))

    loom_left, loom_right = w * 0.09, w * 0.91
    loom_top, loom_bottom = h * 0.18, h * 0.82
    draw.rectangle((loom_left, loom_top, loom_right, loom_bottom), outline=rgba(THREAD, 70), width=2)

    # Punched-card controller.
    card_x, card_y = w * 0.075, h * 0.07
    card_w, card_h = w * 0.33, h * 0.075
    draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=4, fill=rgba((31, 27, 22), 215), outline=rgba(PAPER, 92), width=1)
    shift = (t * 0.55) % (card_w / CARD_COLS)
    cell_w, cell_h = card_w / CARD_COLS, card_h / CARD_ROWS
    for r in range(CARD_ROWS):
        for c in range(CARD_COLS):
            x = card_x + c * cell_w - shift
            if not (card_x <= x <= card_x + card_w):
                continue
            y = card_y + r * cell_h
            if card_pattern[(r + int(t * 2)) % CARD_ROWS, c]:
                draw.ellipse((x + cell_w * 0.28, y + cell_h * 0.22, x + cell_w * 0.72, y + cell_h * 0.78), fill=rgba(AMBER, 118))

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    # Warp threads.
    for i in range(WARP_COUNT):
        u = i / (WARP_COUNT - 1)
        x = loom_left + u * (loom_right - loom_left)
        lift = math.sin(t * 2.4 + warp_phase[i]) * 0.5 + 0.5
        color = CYAN if (i + int(t * 4)) % 13 == 0 else (INDIGO if i % 7 == 0 else THREAD)
        alpha = 38 + 80 * lift
        pts = []
        for j in range(76):
            v = j / 75
            y = loom_top + v * (loom_bottom - loom_top)
            wave = math.sin(v * math.tau * 3 + t * 1.5 + warp_phase[i]) * 3.2
            shed = math.sin((v - loom_phase) * math.tau * 2) * (10 + 10 * lift)
            pts.append((x + wave + shed * (0.4 - abs(u - 0.5)), y))
        draw_thread(od, pts, color, alpha, 1.1)

    # Weft passes.
    for j in range(WEFT_COUNT):
        v = j / (WEFT_COUNT - 1)
        y = loom_top + v * (loom_bottom - loom_top)
        shuttle = (t * 0.36 + j * 0.017) % 1.0
        color = MULBERRY if j % 8 == 0 else (AMBER if j % 11 == 0 else THREAD_DARK)
        alpha = 44 + 56 * (math.sin(t * 1.7 + weft_phase[j]) * 0.5 + 0.5)
        x_end = loom_left + shuttle * (loom_right - loom_left)
        pts = []
        for i in range(86):
            u = i / 85
            x = loom_left + u * (x_end - loom_left)
            interlace = math.sin(u * math.tau * 28 + j * 0.7 + t * 2.2) * 2.3
            pts.append((x, y + interlace))
        draw_thread(od, pts, color, alpha, 1.25)

    # Emerging woven motif.
    for r in range(18):
        for c in range(42):
            u = c / 41
            v = r / 17
            motif = math.sin((u * 5.5 + t * 0.18) * math.tau) + math.cos((v * 4.0 - t * 0.22) * math.tau)
            if motif > 1.18:
                x = loom_left + u * (loom_right - loom_left)
                y = loom_top + v * (loom_bottom - loom_top)
                col = CYAN if motif > 1.55 else AMBER
                od.rectangle((x - 10, y - 3, x + 10, y + 3), fill=rgba(col, 36 + 55 * min(1.0, motif - 1.18)))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.18))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # Shuttle and heddle bars.
    shuttle_x = loom_left + ((t * 0.42) % 1.0) * (loom_right - loom_left)
    draw.rounded_rectangle((shuttle_x - 44, h * 0.50 - 10, shuttle_x + 44, h * 0.50 + 10), radius=6, fill=rgba(AMBER, 120), outline=rgba(PAPER, 130), width=1)
    for k in range(4):
        y = loom_top + (k + 1) / 5 * (loom_bottom - loom_top)
        draw.line((loom_left, y, loom_right, y), fill=rgba(PAPER, 23 + 14 * math.sin(t + k)), width=1)

    for x, y, sp, size in lint:
        px = (x * w + t * (3 + sp * 12)) % w
        py = (y * h + math.sin(t * 0.7 + x * 6) * 3) % h
        col = CYAN if sp > 0.8 else PAPER
        draw.ellipse((px - size * 1.2, py - size * 1.2, px + size * 1.2, py + size * 1.2), fill=rgba(col, 10 + sp * 28))

    draw.text((w * 0.045, h * 0.045), "JACQUARD SIGNAL WEAVE", fill=rgba(PAPER, 130))
    draw.text((w * 0.045, h * 0.074), f"CARD PHASE {loom_phase:0.2f} / THREAD LIFT MAP", fill=rgba(CYAN, 95))
    img.convert("RGB").save(frame_path)


def run() -> None:
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    for frame_no in range(TOTAL_FRAMES):
        render_frame(frame_no, FRAMES_DIR / f"frame-{frame_no + 1:04d}.png")
        if (frame_no + 1) % 60 == 0:
            pct = (frame_no + 1) / TOTAL_FRAMES * 100
            print(f"[Render Progress] Frame {frame_no + 1}/{TOTAL_FRAMES} ({pct:.1f}%)", flush=True)

    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-r",
            str(FPS),
            "-i",
            str(FRAMES_DIR / "frame-%04d.png"),
            "-vf",
            f"scale={OUTPUT_SIZE[0]}:{OUTPUT_SIZE[1]}:flags=lanczos",
            "-vcodec",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ],
        check=True,
    )
    shutil.copyfile(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)
    shutil.rmtree(FRAMES_DIR)
    print("[Render Cleanup] Temporary frames directory successfully removed.")


if __name__ == "__main__":
    run()
