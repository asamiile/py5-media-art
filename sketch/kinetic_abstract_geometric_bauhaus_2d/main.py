from pathlib import Path
import shutil
import subprocess
import sys
import math
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

# Bauhaus palette
COLORS = [
    (210, 40, 40),   # Red
    (30, 80, 180),   # Blue
    (240, 190, 40),  # Yellow
    (30, 30, 30),    # Black
]

class Shape:
    def __init__(self):
        self.type = random.choice(['circle', 'rect', 'triangle', 'arc'])
        self.cx = random.randint(0, SIZE[0])
        self.cy = random.randint(0, SIZE[1])
        self.base_size = random.randint(300, 1500)
        self.color = random.choice(COLORS)
        self.rect_ratio = random.choice([0.2, 0.5, 1.0, 2.0, 5.0])
        
        self.freq_x = random.uniform(0.005, 0.02)
        self.freq_y = random.uniform(0.005, 0.02)
        self.freq_rot = random.uniform(0.002, 0.01)
        
        self.amp_x = random.randint(200, 800)
        self.amp_y = random.randint(200, 800)
        
        self.phase_x = random.uniform(0, py5.TWO_PI)
        self.phase_y = random.uniform(0, py5.TWO_PI)
        self.phase_rot = random.uniform(0, py5.TWO_PI)
        
    def draw(self, t):
        x = self.cx + math.sin(t * self.freq_x + self.phase_x) * self.amp_x
        y = self.cy + math.cos(t * self.freq_y + self.phase_y) * self.amp_y
        rot = math.sin(t * self.freq_rot + self.phase_rot) * py5.TWO_PI
        
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(rot)
        
        py5.no_stroke()
        py5.fill(*self.color)
        
        if self.type == 'circle':
            py5.circle(0, 0, self.base_size)
        elif self.type == 'rect':
            py5.rect_mode(py5.CENTER)
            py5.rect(0, 0, self.base_size, self.base_size * self.rect_ratio)
        elif self.type == 'triangle':
            s = self.base_size / 2
            py5.triangle(0, -s, s, s, -s, s)
        elif self.type == 'arc':
            py5.arc(0, 0, self.base_size, self.base_size, 0, py5.PI)
            
        py5.pop_matrix()

shapes = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    random.seed(1234)
    for _ in range(35):
        shapes.append(Shape())
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(245, 240, 230) 
    
    py5.blend_mode(py5.MULTIPLY)
    
    t = py5.frame_count
    
    for shape in shapes:
        shape.draw(t)

    py5.blend_mode(py5.BLEND)
    
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
