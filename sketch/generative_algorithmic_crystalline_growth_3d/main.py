from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_CRYSTALS = 200

class Crystal:
    def __init__(self):
        self.rot_x = random.uniform(0, py5.TWO_PI)
        self.rot_y = random.uniform(0, py5.TWO_PI)
        self.rot_z = random.uniform(0, py5.TWO_PI)
        
        self.width = random.uniform(20, 80)
        self.height = random.uniform(300, 1000)
        self.depth = random.uniform(20, 80)
        
        self.start_frame = random.randint(0, TOTAL_FRAMES // 2)
        self.growth_duration = random.randint(60, 180)
        
        self.hue = random.choice([190, 220, 280, 310])

crystals = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_CRYSTALS):
        crystals.append(Crystal())

def draw():
    py5.background(10, 20, 15)
    
    # Lighting
    py5.ambient_light(0, 0, 20)
    time_val = py5.frame_count * 0.05
    py5.point_light(200, 50, 100, SIZE[0]/2 + py5.cos(time_val)*500, SIZE[1]/2, 500)
    py5.point_light(300, 50, 100, SIZE[0]/2 - py5.cos(time_val)*500, SIZE[1]/2, -500)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Rotate whole cluster slowly
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.002)
    
    py5.no_stroke()
    
    for c in crystals:
        py5.push_matrix()
        
        py5.rotate_x(c.rot_x)
        py5.rotate_y(c.rot_y)
        py5.rotate_z(c.rot_z)
        
        # Growth animation
        t = (py5.frame_count - c.start_frame) / c.growth_duration
        t = max(0.0, min(1.0, t))
        
        # Smooth step easing
        ease_t = t * t * (3.0 - 2.0 * t)
        
        py5.scale(1.0, ease_t, 1.0)
        
        # Translate so it grows outward from center
        py5.translate(0, c.height * 0.5 * ease_t, 0)
        
        py5.fill(c.hue, 70, 90, 200)
        py5.box(c.width, c.height, c.depth)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
