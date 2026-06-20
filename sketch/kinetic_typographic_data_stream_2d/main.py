from pathlib import Path
import shutil
import subprocess
import sys
import string
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

columns = []
font = None

class DataColumn:
    def __init__(self, x, font_size):
        self.x = x
        self.y = py5.random(-py5.height, 0)
        self.speed = py5.random(5, 25)
        self.chars = []
        self.length = int(py5.random(10, 40))
        self.font_size = font_size
        self.hue = py5.random(160, 200) # cyan/blue theme
        for _ in range(self.length):
            self.chars.append(self.get_random_char())

    def get_random_char(self):
        # mix of hex and symbols
        chars = "0123456789ABCDEF!@#$%^&*()_+-=[]{}|;':,./<>?"
        return py5.random_choice(list(chars))

    def update(self):
        self.y += self.speed
        if self.y > py5.height + self.length * self.font_size:
            self.y = py5.random(-py5.height, 0)
            self.speed = py5.random(5, 25)
            self.length = int(py5.random(10, 40))
            self.hue = py5.random(160, 200)
            self.chars = [self.get_random_char() for _ in range(self.length)]
            
        # Randomly mutate characters
        if py5.random_choice([True, False, False, False]):
            idx = int(py5.random(len(self.chars)))
            self.chars[idx] = self.get_random_char()

    def display(self):
        py5.text_size(self.font_size)
        for i in range(self.length):
            char_y = self.y - (i * self.font_size)
            if 0 < char_y < py5.height + self.font_size:
                # Top character is bright, rest fade out
                alpha = py5.remap(i, 0, self.length, 100, 0)
                if i == 0:
                    py5.fill(0, 0, 100, alpha) # White head
                else:
                    py5.fill(self.hue, 80, 100, alpha)
                py5.text(self.chars[i], self.x, char_y)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    font_size = 24
    py5.text_font(py5.create_font("Courier New", font_size))
    
    num_cols = py5.width // font_size
    for i in range(num_cols):
        columns.append(DataColumn(i * font_size, font_size))

def draw():
    py5.background(5, 100) # slight trail
    
    py5.blend_mode(py5.ADD)
    
    for col in columns:
        col.update()
        col.display()
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
            
        import os
        os._exit(0)

py5.run_sketch()
