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
DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

GRID_WIDTH = 240
GRID_HEIGHT = 135

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    global fuel, heat, wind_x, wind_y

    fuel = np.ones((GRID_HEIGHT, GRID_WIDTH), dtype=np.float32)
    heat = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=np.float32)

    wind_x = np.sin(np.linspace(0, 2*np.pi, GRID_WIDTH)) * 0.3
    wind_y = np.ones(GRID_HEIGHT) * -0.2

    center_y = GRID_HEIGHT - 20
    center_x = GRID_WIDTH // 2
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if 0 <= center_y + dy < GRID_HEIGHT and 0 <= center_x + dx < GRID_WIDTH:
                heat[center_y + dy, center_x + dx] = 1.0

def draw():
    global fuel, heat, wind_x, wind_y

    t = py5.frame_count / FPS

    new_heat = np.zeros_like(heat)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if heat[y, x] > 0.1:
                new_heat[y, x] = max(0, heat[y, x] * 0.92)

                neighbors = [
                    (y-1, x), (y+1, x), (y, x-1), (y, x+1),
                    (y-1, x-1), (y-1, x+1), (y+1, x-1), (y+1, x+1)
                ]

                for ny, nx in neighbors:
                    if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH:
                        if fuel[ny, nx] > 0.1:
                            spread_prob = heat[y, x] * fuel[ny, nx] * 0.85
                            if np.random.random() < spread_prob:
                                new_heat[ny, nx] = max(new_heat[ny, nx], heat[y, x] * 0.9)

                fuel[y, x] = max(0, fuel[y, x] - heat[y, x] * 0.1)

    diffused_heat = heat.copy()
    for y in range(1, GRID_HEIGHT-1):
        for x in range(1, GRID_WIDTH-1):
            neighbors_sum = (heat[y-1, x] + heat[y+1, x] + heat[y, x-1] + heat[y, x+1]) * 0.25
            diffused_heat[y, x] = heat[y, x] * 0.7 + neighbors_sum * 0.3

    heat = np.maximum(diffused_heat, new_heat)

    py5.background(10)
    py5.no_stroke()

    pixel_width = SIZE[0] / GRID_WIDTH
    pixel_height = SIZE[1] / GRID_HEIGHT

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            h = heat[y, x] * (1.0 + fuel[y, x] * 0.1)
            f = fuel[y, x]

            if h > 0.08:
                if h > 0.6:
                    r = int(255)
                    g = int(220 * (h - 0.2) / 0.8)
                    b = int(80 * max(0, (h - 0.4) / 0.6))
                elif h > 0.25:
                    r = int(220 + 35 * (h - 0.25) / 0.35)
                    g = int(120 * (h - 0.25) / 0.35)
                    b = 30
                else:
                    r = int(180 * (h / 0.25))
                    g = int(60 * (h / 0.25))
                    b = 15

                color = py5.color(r, g, b)
                py5.fill(color)
                py5.rect(x * pixel_width, y * pixel_height, pixel_width + 1, pixel_height + 1)
            elif h > 0.02:
                darkness = int(100 * (h / 0.08))
                color = py5.color(darkness // 2, darkness // 4, darkness // 8)
                py5.fill(color)
                py5.rect(x * pixel_width, y * pixel_height, pixel_width + 1, pixel_height + 1)

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
