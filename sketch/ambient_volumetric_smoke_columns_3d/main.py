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

NUM_PARTICLES = 3000

class Particle:
    def __init__(self, is_ember=False):
        self.is_ember = is_ember
        self.reset()
        # Randomize initial Y so they aren't all at the bottom
        self.y = random.uniform(-SIZE[1], SIZE[1])
        
    def reset(self):
        # Spawn near one of a few "columns"
        col = random.choice([-1, 0, 1])
        self.x = col * SIZE[0] * 0.2 + random.gauss(0, SIZE[0] * 0.1)
        self.z = random.gauss(0, SIZE[1] * 0.1)
        self.y = SIZE[1] * 0.8
        
        self.life = random.uniform(0, 1)
        self.life_speed = random.uniform(0.002, 0.005)
        
        if self.is_ember:
            self.size = random.uniform(2, 6)
            self.speed_y = random.uniform(2, 5)
        else:
            self.size = random.uniform(20, 60)
            self.speed_y = random.uniform(0.5, 2)
            
    def update(self, frame):
        self.life += self.life_speed
        if self.life > 1.0 or self.y < -SIZE[1] * 0.8:
            self.reset()
            self.y = SIZE[1] * 0.8
            self.life = 0
            
        # Upward movement
        self.y -= self.speed_y
        
        # Noise-based wind
        noise_x = py5.os_noise(self.x * 0.005, self.y * 0.005, frame * 0.01)
        noise_z = py5.os_noise(self.x * 0.005 + 100, self.y * 0.005, frame * 0.01)
        
        # Spiraling for embers
        if self.is_ember:
            self.x += py5.cos(self.y * 0.05 + frame * 0.1) * 2 + noise_x * 2
            self.z += py5.sin(self.y * 0.05 + frame * 0.1) * 2 + noise_z * 2
        else:
            self.x += noise_x * 3
            self.z += noise_z * 3
            # Smoke expands as it rises
            self.size += 0.2

    def draw(self):
        py5.push_matrix()
        py5.translate(self.x, self.y, self.z)
        
        fade = py5.sin(self.life * py5.PI) # Fade in and out
        
        if self.is_ember:
            py5.fill(30, 80, 100, 200 * fade)
            py5.no_stroke()
            py5.box(self.size)
        else:
            # Additive smoke
            py5.fill(220, 20, 60, 10 * fade)
            py5.no_stroke()
            py5.circle(0, 0, self.size) # 2D circle facing camera
            
        py5.pop_matrix()

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # 5% are embers
    for i in range(NUM_PARTICLES):
        particles.append(Particle(is_ember=(i < NUM_PARTICLES * 0.05)))

def draw():
    py5.background(10, 50, 10) # Dark ambient background
    py5.blend_mode(py5.ADD)
    
    # Camera
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Slow dramatic rotation
    py5.rotate_y(py5.frame_count * 0.005)
    
    # Draw all
    for p in particles:
        p.update(py5.frame_count)
        p.draw()

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
