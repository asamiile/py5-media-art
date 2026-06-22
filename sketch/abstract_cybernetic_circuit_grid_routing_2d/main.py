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

GRID_SPACING = 40
COLS = SIZE[0] // GRID_SPACING + 1
ROWS = SIZE[1] // GRID_SPACING + 1

class Pulse:
    def __init__(self):
        self.cx = random.randint(0, COLS - 1)
        self.cy = random.randint(0, ROWS - 1)
        self.dir = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
        self.history = [(self.cx, self.cy)]
        self.length = random.randint(5, 20)
        self.hue = random.choice([190, 320, 50])  # Cyan, Magenta, Yellow/Gold
        self.speed = 1
        
    def update(self):
        # Move
        self.cx += self.dir[0] * self.speed
        self.cy += self.dir[1] * self.speed
        
        # Wrap around screen
        self.cx %= COLS
        self.cy %= ROWS
        
        self.history.insert(0, (self.cx, self.cy))
        if len(self.history) > self.length:
            self.history.pop()
            
        # Random turns
        if random.random() < 0.1:
            if self.dir[0] != 0: # Moving horizontally
                self.dir = random.choice([(0,1), (0,-1)])
            else: # Moving vertically
                self.dir = random.choice([(1,0), (-1,0)])
                
    def draw(self):
        if len(self.history) < 2:
            return
            
        py5.no_fill()
        py5.stroke_weight(4)
        
        for i in range(len(self.history) - 1):
            p1 = self.history[i]
            p2 = self.history[i+1]
            
            # Don't draw lines that wrap across the screen
            if abs(p1[0] - p2[0]) > 1 or abs(p1[1] - p2[1]) > 1:
                continue
                
            alpha = py5.remap(i, 0, len(self.history), 255, 0)
            
            # Glow effect
            py5.stroke(self.hue, 80, 100, alpha * 0.3)
            py5.stroke_weight(12)
            py5.line(p1[0] * GRID_SPACING, p1[1] * GRID_SPACING, p2[0] * GRID_SPACING, p2[1] * GRID_SPACING)
            
            py5.stroke(self.hue, 50, 100, alpha)
            py5.stroke_weight(4)
            py5.line(p1[0] * GRID_SPACING, p1[1] * GRID_SPACING, p2[0] * GRID_SPACING, p2[1] * GRID_SPACING)

pulses = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(150):
        pulses.append(Pulse())

def draw():
    py5.background(10, 20, 10)
    
    # Draw faint background grid
    py5.stroke(180, 50, 20)
    py5.stroke_weight(1)
    for x in range(COLS):
        py5.line(x * GRID_SPACING, 0, x * GRID_SPACING, SIZE[1])
    for y in range(ROWS):
        py5.line(0, y * GRID_SPACING, SIZE[0], y * GRID_SPACING)
        
    for p in pulses:
        p.update()
        p.draw()

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
