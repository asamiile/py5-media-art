from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 14
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def draw_tree(x, y, angle, depth, length, progress, branches):
    if depth == 0 or length < 1:
        return

    max_depth = 10
    generation_ratio = (max_depth - depth) / max_depth

    if progress < generation_ratio:
        return

    local_progress = (progress - generation_ratio) / (1.0 - generation_ratio)

    end_x = x + length * np.cos(angle)
    end_y = y + length * np.sin(angle)

    end_x = x + (end_x - x) * min(1.0, local_progress * 2)
    end_y = y + (end_y - y) * min(1.0, local_progress * 2)

    thickness = max(1, (max_depth - depth + 1) * 1.5)
    brightness = int(100 + generation_ratio * 120)
    color = py5.color(int(brightness * 0.6), int(brightness * 0.3), int(brightness * 0.1))

    py5.stroke(color)
    py5.stroke_weight(thickness)
    py5.line(x, y, end_x, end_y)

    if local_progress > 0.7:
        leaf_angle1 = angle + np.pi / 2 + np.random.uniform(-0.3, 0.3)
        leaf_angle2 = angle - np.pi / 2 + np.random.uniform(-0.3, 0.3)
        leaf_dist = length * 0.6

        for leaf_angle in [leaf_angle1, leaf_angle2]:
            leaf_x = x + leaf_dist * np.cos(leaf_angle)
            leaf_y = y + leaf_dist * np.sin(leaf_angle)
            py5.no_stroke()
            py5.fill(py5.color(0, 220, 85, 180))
            py5.circle(leaf_x, leaf_y, 3 + generation_ratio * 2)

    branches.append((end_x, end_y, angle, depth, length, progress))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count / FPS
    progress = min(1.0, t / DURATION_SEC)

    py5.background(10, 10, 10)
    py5.no_stroke()

    branches = []

    center_x = SIZE[0] // 2
    center_y = SIZE[1] - 100

    draw_tree(center_x, center_y, -np.pi / 2, 10, 80, progress, branches)

    iteration = 0
    while branches and iteration < 100:
        new_branches = []
        for x, y, angle, depth, length, prog in branches:
            if depth > 0:
                angle1 = angle + 0.4 + np.random.uniform(-0.1, 0.1)
                angle2 = angle - 0.4 + np.random.uniform(-0.1, 0.1)
                new_length = length * 0.75

                draw_tree(x, y, angle1, depth - 1, new_length, prog, new_branches)
                draw_tree(x, y, angle2, depth - 1, new_length, prog, new_branches)
        branches = new_branches
        iteration += 1

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
