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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 5000

class Particle:
    def __init__(self):
        self.x = np.random.uniform(0, SIZE[0])
        self.y = np.random.uniform(0, SIZE[1])
        self.vx = 0
        self.vy = 0
        self.age = 0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    global particles, noise_offset

    particles = [Particle() for _ in range(NUM_PARTICLES)]
    noise_offset = 0

def perlin_velocity(x, y, t):
    scale = 0.003
    speed = 5.0

    angle = py5.noise(x * scale, y * scale, t * 0.05) * 2 * np.pi
    vx = np.cos(angle) * speed
    vy = np.sin(angle) * speed

    return vx, vy

def draw():
    global particles, noise_offset

    t = py5.frame_count / FPS
    noise_offset = t * 0.1

    py5.background(26, 10, 46)
    py5.no_stroke()

    for particle in particles:
        vx, vy = perlin_velocity(particle.x, particle.y, t)

        particle.vx = particle.vx * 0.8 + vx * 0.2
        particle.vy = particle.vy * 0.8 + vy * 0.2

        particle.x += particle.vx
        particle.y += particle.vy
        particle.age += 1

        if particle.x < 0 or particle.x > SIZE[0] or particle.y < 0 or particle.y > SIZE[1]:
            particle.x = np.random.uniform(0, SIZE[0])
            particle.y = np.random.uniform(0, SIZE[1])
            particle.age = 0

        noise_val = py5.noise(particle.x * 0.003, particle.y * 0.003, t * 0.05)

        if noise_val > 0.6:
            r, g, b = 0, 200, 255
        elif noise_val > 0.4:
            r, g, b = 136, 0, 255
        else:
            r, g, b = 255, 0, 255

        alpha = int(200 * (0.5 + 0.5 * noise_val))
        color = py5.color(r, g, b, alpha)
        py5.fill(color)
        py5.circle(particle.x, particle.y, 2 + noise_val * 3)

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
