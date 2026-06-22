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

class DataDrop:
    def __init__(self):
        self.reset()
        self.y = random.uniform(0, SIZE[1]) # Start randomly across screen
        
    def reset(self):
        self.x = random.randint(0, SIZE[0] // 20) * 20
        self.y = random.uniform(-500, -50)
        self.length = random.uniform(20, 150)
        self.speed = random.uniform(10, 40)
        self.hue = random.choice([120, 140, 160, 180, 200]) # Greens to blues
        self.weight = random.uniform(2, 8)
        self.glitch_prob = random.uniform(0, 0.05)
        
    def update(self):
        self.y += self.speed
        
        # Occasional glitch
        if random.random() < self.glitch_prob:
            self.x += random.choice([-20, 20])
            self.hue = 0 # Flash red
            
        if self.y - self.length > SIZE[1]:
            self.reset()
            
    def draw(self):
        py5.stroke(self.hue, 80, 100)
        py5.stroke_weight(self.weight)
        py5.line(self.x, self.y, self.x, self.y - self.length)
        
        # Bright head
        py5.stroke(0, 0, 100)
        py5.point(self.x, self.y)

drops = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
    for _ in range(150):
        drops.append(DataDrop())

def draw():
    # Motion blur / trailing
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    for d in drops:
        d.update()
        d.draw()

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
