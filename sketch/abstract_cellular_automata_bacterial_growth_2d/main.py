from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random
import math

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

MAX_BACTERIA = 1200

class Bacteria:
    def __init__(self, x, y, hue_offset):
        self.x = x
        self.y = y
        self.radius = random.uniform(20, 40)
        self.age = 0
        self.split_age = random.randint(30, 90)
        self.hue_offset = hue_offset
        self.vx = 0
        self.vy = 0
        
    def update(self):
        self.age += 1
        
        # Apply velocity and friction
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.8
        self.vy *= 0.8
        
        # Grow slightly until split
        if self.radius < 50:
            self.radius += 0.2
            
    def draw(self):
        hue = (140 + self.hue_offset + self.age * 0.1) % 360
        py5.fill(hue, 80, 90)
        # Add a darker membrane outline
        py5.stroke(hue, 90, 40)
        py5.stroke_weight(4)
        py5.circle(self.x, self.y, self.radius * 2)

colony = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Start with a few seed bacteria
    for _ in range(10):
        colony.append(Bacteria(SIZE[0]/2 + random.uniform(-100, 100), 
                               SIZE[1]/2 + random.uniform(-100, 100),
                               random.uniform(0, 60)))

def draw():
    py5.background(20, 20, 15)
    
    # Slow drift of the entire colony
    py5.translate(py5.sin(py5.frame_count * 0.01) * 100, py5.cos(py5.frame_count * 0.01) * 100)
    
    new_bacteria = []
    
    # Repulsion physics (O(N^2) but N is small, and we can optimize by only checking close ones roughly)
    # Since pure python might be slow for 1200^2 = 1.4M checks per frame, we'll subsample interactions
    # or just keep N relatively small (e.g. 1200) and it should be okay for a 60fps offline render.
    
    for i, b1 in enumerate(colony):
        for j in range(i + 1, len(colony)):
            b2 = colony[j]
            dx = b1.x - b2.x
            dy = b1.y - b2.y
            dist_sq = dx*dx + dy*dy
            min_dist = b1.radius + b2.radius
            
            if dist_sq < min_dist * min_dist and dist_sq > 0:
                dist = py5.sqrt(dist_sq)
                overlap = min_dist - dist
                
                # Push apart
                force = overlap * 0.05
                fx = (dx / dist) * force
                fy = (dy / dist) * force
                
                b1.vx += fx
                b1.vy += fy
                b2.vx -= fx
                b2.vy -= fy

    # Central attraction to keep them together in a petri dish like blob
    for b in colony:
        dx = SIZE[0]/2 - b.x
        dy = SIZE[1]/2 - b.y
        b.vx += dx * 0.001
        b.vy += dy * 0.001
        
        b.update()
        b.draw()
        
        # Splitting
        if b.age > b.split_age and len(colony) + len(new_bacteria) < MAX_BACTERIA:
            b.age = 0
            b.radius *= 0.7
            
            # Create child
            child = Bacteria(b.x + random.uniform(-10, 10), b.y + random.uniform(-10, 10), b.hue_offset + random.uniform(-10, 10))
            child.radius = b.radius
            
            # Push apart strongly
            child.vx = random.uniform(-5, 5)
            child.vy = random.uniform(-5, 5)
            b.vx = -child.vx
            b.vy = -child.vy
            
            new_bacteria.append(child)
            
    colony.extend(new_bacteria)

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
