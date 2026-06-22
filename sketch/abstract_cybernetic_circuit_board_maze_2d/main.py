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

GRID_SIZE = 40
NUM_TRACERS = 150

class Tracer:
    def __init__(self):
        self.reset()
        
    def reset(self):
        # Snap to grid
        self.x = (random.randint(0, SIZE[0] // GRID_SIZE)) * GRID_SIZE
        self.y = (random.randint(0, SIZE[1] // GRID_SIZE)) * GRID_SIZE
        self.history = [(self.x, self.y)]
        
        # 0: Right, 1: Down, 2: Left, 3: Up
        self.dir = random.randint(0, 3)
        self.speed = 10
        self.hue = random.choice([160, 200, 320, 50])
        self.life = random.randint(20, 100)
        self.age = 0
        self.dead = False

    def update(self):
        if self.dead:
            return
            
        self.age += 1
        if self.age > self.life:
            self.dead = True
            return
            
        # Move
        if self.dir == 0: self.x += self.speed
        elif self.dir == 1: self.y += self.speed
        elif self.dir == 2: self.x -= self.speed
        elif self.dir == 3: self.y -= self.speed
        
        self.history.append((self.x, self.y))
        
        # Turn randomly at grid intersections
        if self.x % GRID_SIZE == 0 and self.y % GRID_SIZE == 0:
            if random.random() < 0.3:
                # Turn 90 degrees
                self.dir = (self.dir + random.choice([-1, 1])) % 4

tracers = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0, 0, 5) # Very dark

    for _ in range(NUM_TRACERS):
        tracers.append(Tracer())

def draw():
    # Subtle fade to create trails
    py5.no_stroke()
    py5.fill(0, 0, 5, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    for t in tracers:
        t.update()
        
        # Draw the tracer trail
        if len(t.history) > 1:
            py5.stroke(t.hue, 80, 100, 100)
            py5.stroke_weight(2)
            
            hx, hy = t.history[-2]
            nx, ny = t.history[-1]
            py5.line(hx, hy, nx, ny)
            
            # Glow effect at the head
            if not t.dead:
                pulse = py5.sin(py5.frame_count * 0.2 + t.age) * 0.5 + 0.5
                py5.fill(t.hue, 50, 100, 200 * pulse)
                py5.no_stroke()
                py5.circle(nx, ny, 6 + pulse * 6)
                
        # Revive dead tracers over time to keep scene active
        if t.dead and random.random() < 0.05:
            t.reset()

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
