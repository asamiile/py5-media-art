from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math
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

NUM_PARTICLES = 15000

class Pole:
    def __init__(self, charge):
        self.charge = charge # +1 or -1
        self.offset = random.uniform(0, 1000)
        self.speed = random.uniform(0.002, 0.005)
        self.radius = random.uniform(200, 600)
        
    def position(self, t):
        cx = SIZE[0] / 2
        cy = SIZE[1] / 2
        x = cx + py5.cos(t * self.speed + self.offset) * self.radius
        y = cy + py5.sin(t * self.speed * 1.3 + self.offset) * self.radius
        return x, y

class Particle:
    def __init__(self):
        self.x = random.uniform(0, SIZE[0])
        self.y = random.uniform(0, SIZE[1])
        self.vx = 0
        self.vy = 0
        self.life = random.randint(50, 200)
        
    def update(self, poles, t):
        fx = 0
        fy = 0
        for p in poles:
            px, py_pos = p.position(t)
            dx = self.x - px
            dy = self.y - py_pos
            dist_sq = dx*dx + dy*dy
            if dist_sq < 1:
                dist_sq = 1
            # Inverse square law
            force = p.charge / dist_sq * 10000.0
            
            # Unit vector
            dist = math.sqrt(dist_sq)
            ux = dx / dist
            uy = dy / dist
            
            fx += ux * force
            fy += uy * force
            
        # Magnetic field lines don't push particles, they ALIGN them.
        # But we can move particles along the lines.
        angle = math.atan2(fy, fx)
        
        speed = 4.0
        self.vx = py5.cos(angle) * speed
        self.vy = py5.sin(angle) * speed
        
        self.x += self.vx
        self.y += self.vy
        
        self.life -= 1
        if self.life < 0 or self.x < 0 or self.x > SIZE[0] or self.y < 0 or self.y > SIZE[1]:
            self.x = random.uniform(0, SIZE[0])
            self.y = random.uniform(0, SIZE[1])
            self.life = random.randint(50, 200)

poles = []
particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    poles.append(Pole(1))
    poles.append(Pole(-1))
    poles.append(Pole(1))
    poles.append(Pole(-1))
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Accumulate trails
    py5.fill(10, 15, 20, 15)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count
    
    py5.stroke(220, 80, 100, 50)
    py5.stroke_weight(2)
    
    for p in particles:
        p.update(poles, t)
        
        # Color based on direction
        angle = math.atan2(p.vy, p.vx)
        hue = py5.remap(angle, -math.pi, math.pi, 180, 300)
        py5.stroke(hue, 80, 100, 50)
        
        py5.point(p.x, p.y)

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
