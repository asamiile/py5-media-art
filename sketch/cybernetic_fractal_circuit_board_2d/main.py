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

class Node:
    def __init__(self, x, y, angle, depth, max_depth):
        self.x = x
        self.y = y
        self.angle = angle
        self.depth = depth
        self.max_depth = max_depth
        self.length = 0
        self.target_length = random.uniform(20, 100) * (0.9 ** depth)
        self.active = True
        self.children = []
        self.thickness = max(1, 8 - depth * 1.5)
        self.is_leaf = False

    def update(self):
        if self.active:
            self.length += 3.0  # growth speed
            if self.length >= self.target_length:
                self.length = self.target_length
                self.active = False
                self.branch()
        for child in self.children:
            child.update()

    def branch(self):
        if self.depth >= self.max_depth:
            self.is_leaf = True
            return
        
        # Branch into 1 to 3 new nodes
        num_branches = random.choice([1, 2, 2, 3])
        angles = []
        
        if num_branches == 1:
            angles = [self.angle + random.choice([-py5.HALF_PI, py5.HALF_PI, py5.QUARTER_PI, -py5.QUARTER_PI])]
        elif num_branches == 2:
            base = self.angle
            angles = [base + py5.HALF_PI, base - py5.HALF_PI]
            if random.random() < 0.5:
                angles = [base + py5.QUARTER_PI, base - py5.QUARTER_PI]
        else:
            base = self.angle
            angles = [base, base + py5.HALF_PI, base - py5.HALF_PI]

        end_x = self.x + py5.cos(self.angle) * self.length
        end_y = self.y + py5.sin(self.angle) * self.length

        for a in angles:
            self.children.append(Node(end_x, end_y, a, self.depth + 1, self.max_depth))

    def draw(self):
        end_x = self.x + py5.cos(self.angle) * self.length
        end_y = self.y + py5.sin(self.angle) * self.length
        
        py5.stroke_weight(self.thickness)
        py5.stroke(45, 80, 100, 200) # Gold color
        py5.line(self.x, self.y, end_x, end_y)
        
        if self.is_leaf or self.length >= self.target_length:
            py5.fill(190, 100, 100, 255) # Cyan data point
            py5.no_stroke()
            py5.circle(end_x, end_y, self.thickness * 2.5)

        for child in self.children:
            child.draw()

roots = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(220, 90, 10) # Dark blue background
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize roots
    for i in range(4):
        roots.append(Node(SIZE[0]/2, SIZE[1]/2, i * py5.HALF_PI, 0, 7))

def draw():
    py5.background(220, 90, 10, 40) # Slight trail effect
    
    for root in roots:
        root.update()
        root.draw()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
