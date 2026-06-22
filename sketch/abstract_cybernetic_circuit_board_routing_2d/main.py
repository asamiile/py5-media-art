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
COLS = SIZE[0] // GRID_SIZE
ROWS = SIZE[1] // GRID_SIZE

grid = [[0 for _ in range(ROWS)] for _ in range(COLS)]

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.connected = False
        
class Trace:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.history = [(x, y)]
        self.active = True
        self.hue = random.choice([160, 200, 320, 60])
        self.speed = random.randint(1, 3)
        self.length = random.randint(10, 50)
        
    def update(self):
        if not self.active: return
        
        for _ in range(self.speed):
            if not self.active: break
            
            nx = self.x + self.dx
            ny = self.y + self.dy
            
            if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
                self.active = False
                break
                
            if grid[nx][ny] == 1:
                self.active = False
                break
                
            self.x = nx
            self.y = ny
            grid[nx][ny] = 1
            self.history.append((self.x, self.y))
            
            # Randomly turn 45 or 90 degrees
            if random.random() < 0.1:
                options = [(self.dy, -self.dx), (-self.dy, self.dx)]
                # Add diagonal options
                if self.dx == 0:
                    options.append((1, self.dy))
                    options.append((-1, self.dy))
                elif self.dy == 0:
                    options.append((self.dx, 1))
                    options.append((self.dx, -1))
                else:
                    options.append((self.dx, 0))
                    options.append((0, self.dy))
                self.dx, self.dy = random.choice(options)
                
nodes = []
traces = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(10, 15, 20)
    
    # Spawn initial nodes
    for _ in range(50):
        nx, ny = random.randint(2, COLS-3), random.randint(2, ROWS-3)
        nodes.append(Node(nx, ny))
        grid[nx][ny] = 2
        
        # Spawn traces from nodes
        for _ in range(random.randint(1, 4)):
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)])
            traces.append(Trace(nx, ny, dx, dy))

def draw():
    # Only draw the new segments to save performance, but we want glowing pulses
    # We will redraw everything
    py5.background(10, 15, 20, 40)
    
    time_val = py5.frame_count * 0.1
    
    py5.stroke_cap(py5.SQUARE)
    py5.stroke_join(py5.MITER)
    
    for t in traces:
        t.update()
        if len(t.history) < 2: continue
        
        # Draw trace
        py5.no_fill()
        py5.stroke(t.hue, 80, 50)
        py5.stroke_weight(4)
        py5.begin_shape()
        for px, py_pos in t.history:
            py5.vertex(px * GRID_SIZE, py_pos * GRID_SIZE)
        py5.end_shape()
        
        # Draw pulsing glow on active traces
        if t.active:
            pulse = (py5.sin(time_val + len(t.history)) + 1) / 2
            py5.stroke(t.hue, 80, 100, 150 * pulse)
            py5.stroke_weight(8)
            py5.begin_shape()
            # Only glow the last few segments
            recent = t.history[-10:]
            for px, py_pos in recent:
                py5.vertex(px * GRID_SIZE, py_pos * GRID_SIZE)
            py5.end_shape()
            
    # Draw nodes
    for n in nodes:
        py5.fill(0, 0, 100)
        py5.no_stroke()
        py5.rect(n.x * GRID_SIZE - 4, n.y * GRID_SIZE - 4, 8, 8)
        py5.no_fill()
        py5.stroke(0, 0, 100, 100)
        py5.stroke_weight(2)
        py5.circle(n.x * GRID_SIZE, n.y * GRID_SIZE, 20)

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
