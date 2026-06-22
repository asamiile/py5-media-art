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

GRID_SIZE = 40
NUM_SPARKS = 80

class Spark:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.randint(0, SIZE[0] // GRID_SIZE) * GRID_SIZE
        self.y = random.randint(0, SIZE[1] // GRID_SIZE) * GRID_SIZE
        self.px = self.x
        self.py = self.y
        
        # Directions: 0=R, 1=D, 2=L, 3=U
        self.dir = random.randint(0, 3)
        self.speed = GRID_SIZE // 4 # Must divide evenly into grid size
        self.hue = random.choice([180, 200, 320, 60]) # Cyan, Blue, Pink, Yellow
        self.life = random.randint(100, 300)
        
    def update(self):
        self.px = self.x
        self.py = self.y
        
        # Move
        if self.dir == 0: self.x += self.speed
        elif self.dir == 1: self.y += self.speed
        elif self.dir == 2: self.x -= self.speed
        elif self.dir == 3: self.y -= self.speed
        
        self.life -= 1
        
        # Change direction only on grid intersections
        if self.x % GRID_SIZE == 0 and self.y % GRID_SIZE == 0:
            if random.random() < 0.4:
                # Turn 90 degrees
                self.dir = (self.dir + random.choice([-1, 1])) % 4
                
            # Random chance to split / change color
            if random.random() < 0.1:
                self.hue = (self.hue + random.choice([20, -20])) % 360
        
        # Out of bounds check
        if self.x < 0 or self.x > SIZE[0] or self.y < 0 or self.y > SIZE[1] or self.life <= 0:
            self.reset()
            self.px = self.x
            self.py = self.y

    def draw(self):
        py5.stroke(self.hue, 80, 100, 200)
        py5.stroke_weight(3)
        py5.line(self.px, self.py, self.x, self.y)
        
        # Draw bright head
        py5.fill(0, 0, 100)
        py5.no_stroke()
        py5.circle(self.x, self.y, 6)

sparks = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_SPARKS):
        sparks.append(Spark())
        
    # Draw dark grid background once
    py5.background(10, 10, 5)
    py5.stroke(200, 50, 20, 40)
    py5.stroke_weight(1)
    for x in range(0, SIZE[0], GRID_SIZE):
        py5.line(x, 0, x, SIZE[1])
    for y in range(0, SIZE[1], GRID_SIZE):
        py5.line(0, y, SIZE[0], y)

def draw():
    # Motion blur for trails
    py5.no_stroke()
    py5.fill(10, 10, 5, 10)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    for s in sparks:
        s.update()
        s.draw()

    py5.blend_mode(py5.BLEND)

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
