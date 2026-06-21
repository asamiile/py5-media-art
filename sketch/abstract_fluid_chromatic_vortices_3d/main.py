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

NUM_PARTICLES = 3000

class Particle:
    def __init__(self):
        self.angle = random.uniform(0, py5.TWO_PI)
        self.radius = random.uniform(50, SIZE[1] * 0.8)
        self.z = random.uniform(-SIZE[1]/2, SIZE[1]/2)
        self.speed = random.uniform(0.01, 0.05)
        self.size = random.uniform(2, 6)
        self.color_offset = random.uniform(0, 360)
        
    def update(self, frame):
        # Move inward slightly and rotate
        self.radius -= py5.sin(frame * 0.01 + self.angle) * 2
        if self.radius < 10:
            self.radius = SIZE[1] * 0.8 # Reset to outer edge
            self.z = random.uniform(-SIZE[1]/2, SIZE[1]/2)
            
        self.angle += self.speed * (1.0 + (SIZE[1]*0.8 - self.radius)/100.0) # Faster near center
        
        # Swirl effect based on Z
        z_effect = py5.sin(self.z * 0.01 + frame * 0.02) * 50
        
        self.x = py5.cos(self.angle) * (self.radius + z_effect)
        self.y = py5.sin(self.angle) * (self.radius + z_effect)
        
    def draw(self, frame):
        py5.push_matrix()
        py5.translate(self.x, self.y, self.z)
        
        hue = (self.color_offset + frame * 0.5 + self.radius * 0.5) % 360
        py5.fill(hue, 90, 100, 150)
        py5.no_stroke()
        py5.circle(0, 0, self.size)
        py5.pop_matrix()

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Partial background for trails
    py5.push_matrix()
    py5.translate(0, 0, -SIZE[1])
    py5.fill(0, 0, 5, 40) # Very dark, somewhat transparent
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0]*3, SIZE[1]*3)
    py5.pop_matrix()
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Camera orbital
    py5.rotate_x(py5.sin(py5.frame_count * 0.005) * py5.PI/4)
    py5.rotate_y(py5.frame_count * 0.01)
    
    for p in particles:
        p.update(py5.frame_count)
        p.draw(py5.frame_count)
        
    py5.blend_mode(py5.BLEND) # Reset blend mode for next frame's background
    
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
