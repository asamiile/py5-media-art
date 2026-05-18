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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

GRID_WIDTH = 200
GRID_HEIGHT = 120

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    global height, velocity, damping

    height = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=np.float32)
    velocity = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=np.float32)
    damping = 0.975

    center_y, center_x = GRID_HEIGHT // 2, GRID_WIDTH // 2
    radius = 5
    for y in range(max(0, center_y - radius), min(GRID_HEIGHT, center_y + radius + 1)):
        for x in range(max(0, center_x - radius), min(GRID_WIDTH, center_x + radius + 1)):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            if dist <= radius:
                height[y, x] = 2.0 * (1.0 - dist / radius)

def draw():
    global height, velocity

    t = py5.frame_count / FPS

    new_height = height.copy()

    for y in range(1, GRID_HEIGHT - 1):
        for x in range(1, GRID_WIDTH - 1):
            laplacian = (height[y-1, x] + height[y+1, x] + height[y, x-1] + height[y, x+1] - 4 * height[y, x])
            acceleration = laplacian * 0.15
            velocity[y, x] = (velocity[y, x] + acceleration) * damping
            new_height[y, x] = height[y, x] + velocity[y, x]

    if py5.frame_count % 120 == 0 and py5.frame_count < TOTAL_FRAMES * 0.6:
        center_y = GRID_HEIGHT // 2
        center_x = GRID_WIDTH // 2
        radius = 3
        for y in range(max(0, center_y - radius), min(GRID_HEIGHT, center_y + radius + 1)):
            for x in range(max(0, center_x - radius), min(GRID_WIDTH, center_x + radius + 1)):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist <= radius:
                    new_height[y, x] += 0.5 * (1.0 - dist / radius)

    height = new_height

    py5.background(13, 27, 61)
    py5.no_stroke()

    pixel_width = SIZE[0] / GRID_WIDTH
    pixel_height = SIZE[1] / GRID_HEIGHT

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            h = height[y, x]

            if h > 0.08:
                brightness = min(255, int(220 + h * 250))
                color = py5.color(int(brightness * 0.4), int(brightness * 0.8), brightness)
            elif h > 0.02:
                brightness = int(140 + h * 180)
                color = py5.color(int(brightness * 0.3), int(brightness * 0.6), int(brightness * 0.9))
            elif h > -0.08:
                base_ocean = int(40 + abs(h) * 120)
                color = py5.color(int(base_ocean * 0.3), int(base_ocean * 0.5), int(base_ocean * 0.7))
            else:
                base_ocean = int(60 + abs(h) * 100)
                color = py5.color(int(base_ocean * 0.25), int(base_ocean * 0.4), int(base_ocean * 0.6))

            py5.fill(color)
            py5.rect(x * pixel_width, y * pixel_height, pixel_width + 1, pixel_height + 1)

            if h > 0.1 and np.random.random() < 0.3:
                foam_brightness = int(255 * (h / 0.5))
                py5.fill(py5.color(200, 220, 255, 100))
                foam_size = (h / 0.5) * 2
                py5.circle(x * pixel_width + pixel_width / 2, y * pixel_height + pixel_height / 2, foam_size)

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
