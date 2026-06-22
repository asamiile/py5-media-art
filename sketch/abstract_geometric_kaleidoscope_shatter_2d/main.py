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

NUM_SLICES = 12
ANGLE = (py5.PI * 2) / NUM_SLICES

class Shard:
    def __init__(self):
        self.points = []
        num_pts = random.randint(3, 5)
        self.r_center = random.uniform(50, 400)
        self.a_center = random.uniform(0, ANGLE)
        
        for _ in range(num_pts):
            r = self.r_center + random.uniform(-100, 100)
            a = self.a_center + random.uniform(-0.2, 0.2)
            self.points.append((r, a))
            
        self.hue = random.choice([200, 320, 40, 280, 160])
        self.sat = random.uniform(60, 100)
        self.bri = random.uniform(80, 100)
        
        # Movement speeds
        self.r_speed = random.uniform(-1, 1)
        self.a_speed = random.uniform(-0.01, 0.01)
        
    def update(self):
        # Rotate and drift the shard
        self.a_center += self.a_speed
        self.r_center += py5.sin(py5.frame_count * 0.05) * self.r_speed
        
    def draw(self):
        py5.fill(self.hue, self.sat, self.bri, 200)
        py5.stroke(360, 0, 100, 150)
        py5.stroke_weight(2)
        
        py5.begin_shape()
        for i, (r_offset, a_offset) in enumerate(self.points):
            # Recalculate relative to moving center
            r = r_offset + (self.r_center - r_offset)*0.1 # Soft constraint
            a = self.a_center + (a_offset - self.a_center)
            
            x = py5.cos(a) * r
            y = py5.sin(a) * r
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

shards = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(50):
        shards.append(Shard())

def draw():
    py5.background(15, 10, 15)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    # Global rotation
    py5.rotate(py5.frame_count * 0.005)
    
    for s in shards:
        s.update()
        
    # Draw kaleidoscope slices
    for i in range(NUM_SLICES):
        py5.push_matrix()
        py5.rotate(i * ANGLE)
        
        # Alternate reflection for true kaleidoscope
        if i % 2 == 1:
            py5.scale(1.0, -1.0)
            
        for s in shards:
            s.draw()
            
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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
