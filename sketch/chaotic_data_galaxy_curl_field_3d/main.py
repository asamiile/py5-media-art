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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        # Start in a sphere
        r = random.uniform(100, 800)
        theta = random.uniform(0, py5.TWO_PI)
        phi = random.uniform(0, py5.PI)
        
        self.x = r * math.sin(phi) * math.cos(theta)
        self.y = r * math.sin(phi) * math.sin(theta)
        self.z = r * math.cos(phi)
        
        self.vx = 0
        self.vy = 0
        self.vz = 0
        
        self.history = []
        self.hue = random.choice([20, 320, 200]) # Orange, Pink, Ice Blue
        self.life = random.randint(50, 150)

particles = []
num_particles = 3000

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    for _ in range(num_particles):
        particles.append(Particle())

def curl_noise(x, y, z, t):
    eps = 0.1
    # Very simple approximation of curl noise using 3D noise
    n1 = py5.noise(x, y + eps, z, t) - py5.noise(x, y - eps, z, t)
    n2 = py5.noise(x, y, z + eps, t) - py5.noise(x, y, z - eps, t)
    n3 = py5.noise(x + eps, y, z, t) - py5.noise(x - eps, y, z, t)
    
    cx = n2 - n1
    cy = n3 - py5.noise(x, y, z + eps, t)
    cz = py5.noise(x, y + eps, z, t) - n3
    return cx, cy, cz

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    time = py5.frame_count * 0.01
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    for p in particles:
        # Simulate curl noise
        nx = p.x * 0.005
        ny = p.y * 0.005
        nz = p.z * 0.005
        
        # In py5 noise is up to 3D. We use t for the Z component and z for the Y component to fake it
        dx = py5.noise(ny, nz, time) - 0.5
        dy = py5.noise(nx, nz, time + 100) - 0.5
        dz = py5.noise(nx, ny, time + 200) - 0.5
        
        force_mult = py5.remap(math.sin(time * 5), -1, 1, 5, 20)
        
        p.vx += dx * force_mult
        p.vy += dy * force_mult
        p.vz += dz * force_mult
        
        # Friction
        p.vx *= 0.9
        p.vy *= 0.9
        p.vz *= 0.9
        
        p.x += p.vx
        p.y += p.vy
        p.z += p.vz
        
        p.history.append((p.x, p.y, p.z))
        if len(p.history) > 10:
            p.history.pop(0)
            
        p.life -= 1
        if p.life <= 0:
            p.reset()
            
        # Draw trail
        alpha = py5.remap(p.life, 0, 150, 0, 200)
        if alpha > 0:
            py5.stroke(p.hue, 80, 100, alpha)
            py5.begin_shape(py5.LINE_STRIP)
            for pos in p.history:
                py5.vertex(pos[0], pos[1], pos[2])
            py5.end_shape()

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
