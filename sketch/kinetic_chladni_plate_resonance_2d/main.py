from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Particle parameters
NUM_PARTICLES = 15000
particles = []

def chladni(x, y, n, m, L):
    # Normalized coordinates -0.5 to 0.5
    nx = x / L - 0.5
    ny = y / L - 0.5
    # Chladni equation
    v1 = math.cos(n * math.pi * nx) * math.cos(m * math.pi * ny)
    v2 = math.cos(m * math.pi * nx) * math.cos(n * math.pi * ny)
    return abs(v1 - v2)

class Particle:
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = 0.0
        self.vy = 0.0

    def update(self, n, m, L, t):
        # Calculate gradient using central difference
        eps = 1.0
        c = chladni(self.x, self.y, n, m, L)
        cx = chladni(self.x + eps, self.y, n, m, L)
        cy = chladni(self.x, self.y + eps, n, m, L)
        
        grad_x = (cx - c) / eps
        grad_y = (cy - c) / eps
        
        # Move towards nodes (where amplitude is 0)
        # So we move in the negative gradient direction
        force = 5.0
        self.vx -= grad_x * force
        self.vy -= grad_y * force
        
        # Damping
        self.vx *= 0.8
        self.vy *= 0.8
        
        # Add a tiny bit of random brownian motion related to the amplitude
        # So particles jitter when they are not at the nodes, and settle at the nodes
        jitter = c * 3.0
        self.x += self.vx + random.uniform(-jitter, jitter)
        self.y += self.vy + random.uniform(-jitter, jitter)
        
        # Wrap around
        if self.x < 0: self.x += L
        if self.x > L: self.x -= L
        if self.y < 0: self.y += L
        if self.y > L: self.y -= L

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle(py5.width, py5.height))

def draw():
    # Draw background with slight transparency for motion blur
    py5.fill(10, 80, 15, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Smoothly transition between modes
    # Start at n=3, m=5, transition to n=5, m=2
    n = py5.remap(math.sin(t * math.pi), 0, 1, 3.0, 5.0)
    m = py5.remap(math.cos(t * math.pi * 2), -1, 1, 2.0, 5.0)
    
    # Sand color
    py5.fill(40, 60, 100, 150)
    
    L = min(py5.width, py5.height)
    
    # Scale to fill screen
    scale_factor = max(py5.width, py5.height) / float(L)
    
    for p in particles:
        p.update(n, m, L, t)
        
        # Draw particle
        # Add some glow based on velocity
        v = math.sqrt(p.vx*p.vx + p.vy*p.vy)
        h = (40 + v * 10) % 360
        py5.fill(h, 60 - v*5, 100, 180)
        
        # Map back to screen
        sx = p.x * scale_factor
        sy = p.y * scale_factor
        py5.circle(sx, sy, 3)

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
