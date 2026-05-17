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
DURATION_SEC = 16
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

class Cell:
    def __init__(self, x, y, generation, parent_angle=0):
        self.x = x
        self.y = y
        self.generation = generation
        self.radius = max(2, 20 - generation * 2.5)
        self.age = 0
        self.max_age = 120 - generation * 8
        self.parent_angle = parent_angle
        self.has_divided = False
        self.children = []

    def get_color(self):
        gen_ratio = min(1.0, self.generation / 8.0)
        r = int(0 + gen_ratio * 50)
        g = int(180 - gen_ratio * 80)
        b = int(70 + gen_ratio * 150)

        if self.generation % 2 == 0:
            g = min(255, g + 20)
        else:
            b = min(255, b + 20)

        return py5.color(r, g, b)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    global cells, next_cell_id

    cells = []
    next_cell_id = 0

    center_x, center_y = SIZE[0] // 2, SIZE[1] // 2
    cells.append(Cell(center_x, center_y, 0))

def draw():
    global cells, next_cell_id

    t = py5.frame_count / FPS

    py5.background(245, 245, 240)
    py5.no_stroke()

    for cell in cells[:]:
        cell.age += 1

        if cell.age > cell.max_age:
            cells.remove(cell)
            continue

        progress = cell.age / cell.max_age

        if not cell.has_divided and progress > 0.6 and cell.generation < 8:
            cell.has_divided = True

            angle1 = cell.parent_angle + np.random.uniform(-0.3, 0.3)
            angle2 = cell.parent_angle + np.pi + np.random.uniform(-0.3, 0.3)
            distance = cell.radius * 1.8

            child1_x = cell.x + np.cos(angle1) * distance
            child1_y = cell.y + np.sin(angle1) * distance
            child2_x = cell.x + np.cos(angle2) * distance
            child2_y = cell.y + np.sin(angle2) * distance

            if 0 <= child1_x < SIZE[0] and 0 <= child1_y < SIZE[1]:
                child1 = Cell(child1_x, child1_y, cell.generation + 1, angle1)
                cells.append(child1)
                cell.children.append(child1)

            if 0 <= child2_x < SIZE[0] and 0 <= child2_y < SIZE[1]:
                child2 = Cell(child2_x, child2_y, cell.generation + 1, angle2)
                cells.append(child2)
                cell.children.append(child2)

        brightness_mult = 1.0 - (abs(progress - 0.5) * 2) * 0.3

        color = cell.get_color()
        py5.fill(color, int(200 * brightness_mult))

        pulse = 1.0 + np.sin(progress * np.pi * 4) * 0.2
        radius = cell.radius * pulse

        py5.circle(cell.x, cell.y, radius)

        if cell.generation > 0 and cell.age < 40:
            py5.fill(py5.color(50, 30, 80), int(100 * (1.0 - cell.age / 40)))
            nucleus_size = radius * 0.4
            py5.circle(cell.x, cell.y, nucleus_size)

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
