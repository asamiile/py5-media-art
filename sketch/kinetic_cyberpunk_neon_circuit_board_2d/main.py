from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5

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

class Tracer:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.active = True
        self.hue = random.choice([180, 320, 40])
        self.history = [(x, y)]
        self.length = random.randint(10, 50)
        self.step_size = py5.width / 100

    def update(self):
        if not self.active:
            return
            
        if random.random() < 0.2:
            self.direction += random.choice([-py5.PI/2, py5.PI/2, 0])
            
        self.x += py5.cos(self.direction) * self.step_size
        self.y += py5.sin(self.direction) * self.step_size
        
        self.history.append((self.x, self.y))
        
        if len(self.history) > self.length or self.x < 0 or self.x > py5.width or self.y < 0 or self.y > py5.height:
            self.active = False
            
    def draw(self):
        py5.stroke(self.hue, 80, 100, 80)
        py5.stroke_weight(3)
        py5.no_fill()
        py5.begin_shape()
        for hx, hy in self.history:
            py5.vertex(hx, hy)
        py5.end_shape()
        
        # Draw glowing node at head if active
        if self.active:
            py5.no_stroke()
            py5.fill(self.hue, 80, 100, 100)
            py5.circle(self.x, self.y, 8)

tracers = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    
    for _ in range(5):
        spawn_tracer()

def spawn_tracer():
    x = int(random.randint(0, 100)) * (py5.width / 100)
    y = int(random.randint(0, 100)) * (py5.height / 100)
    direction = random.choice([0, py5.PI/2, py5.PI, py5.PI*1.5])
    tracers.append(Tracer(x, y, direction))

def draw():
    # Fade background slightly for motion blur
    py5.background(220, 80, 5, 20)
    
    if py5.frame_count % 10 == 0 and len(tracers) < 100:
        spawn_tracer()
        
    for tracer in tracers:
        tracer.update()
        tracer.draw()
        
    # Remove dead tracers occasionally to keep performance up
    if py5.frame_count % 60 == 0:
        tracers[:] = [t for t in tracers if t.active]

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
            
        import os
        os._exit(0)

py5.run_sketch()
