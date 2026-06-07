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

FISH = []
NUM_FISH = 300

class GlassFish:
    def __init__(self, i):
        self.i = i
        self.pos = py5.Py5Vector(random.uniform(-SIZE[0], SIZE[0]), 
                                 random.uniform(-SIZE[1], SIZE[1]), 
                                 random.uniform(-SIZE[0], SIZE[0]))
        self.vel = py5.Py5Vector(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
        self.vel.normalize()
        self.vel *= random.uniform(2, 6)
        
        self.size = random.uniform(20, 60)
        self.hue = py5.random(180, 220) if random.random() > 0.2 else py5.random(280, 320)
        
    def update(self, frame_count):
        # Steer using noise field
        nx = py5.os_noise(self.pos.x * 0.002, self.pos.y * 0.002, frame_count * 0.005) - 0.5
        ny = py5.os_noise(self.pos.x * 0.002 + 100, self.pos.y * 0.002 + 100, frame_count * 0.005) - 0.5
        nz = py5.os_noise(self.pos.x * 0.002 + 200, self.pos.y * 0.002 + 200, frame_count * 0.005) - 0.5
        
        steer = py5.Py5Vector(nx, ny, nz)
        steer.normalize()
        steer *= 0.2
        
        self.vel += steer
        self.vel.normalize()
        self.vel *= 8  # Constant speed
        
        self.pos += self.vel
        
        # Wrap around
        bound = 1500
        if self.pos.x > bound: self.pos.x = -bound
        elif self.pos.x < -bound: self.pos.x = bound
        if self.pos.y > bound: self.pos.y = -bound
        elif self.pos.y < -bound: self.pos.y = bound
        if self.pos.z > bound: self.pos.z = -bound
        elif self.pos.z < -bound: self.pos.z = bound

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(NUM_FISH):
        FISH.append(GlassFish(i))

def draw():
    py5.background(10, 100, 10) # Dark deep cyber ocean blue
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    # Slow rotation
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_x(py5.sin(py5.frame_count * 0.005) * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Lighting for glass effect
    py5.ambient_light(200, 50, 50)
    py5.directional_light(200, 80, 100, 1, 1, -1)
    py5.directional_light(300, 80, 100, -1, -1, 1)
    py5.specular(0, 0, 100)
    py5.shininess(50)
    
    py5.no_stroke()
    
    for fish in FISH:
        fish.update(py5.frame_count)
        
        py5.push_matrix()
        py5.translate(fish.pos.x, fish.pos.y, fish.pos.z)
        
        # Align fish to velocity
        heading = py5.atan2(fish.vel.y, fish.vel.x)
        pitch = py5.asin(-fish.vel.z / fish.vel.mag)
        
        py5.rotate_y(-pitch)
        py5.rotate_z(heading)
        
        # Tail wag
        wag = py5.sin(py5.frame_count * 0.2 + fish.i) * 0.3
        py5.rotate_y(wag)
        
        py5.fill(fish.hue, 80, 100, 40)
        
        # Draw fish body (diamond shape)
        py5.begin_shape(py5.TRIANGLES)
        
        l = fish.size
        w = fish.size * 0.3
        h = fish.size * 0.5
        
        # Left side
        py5.vertex(l, 0, 0)
        py5.vertex(0, w, 0)
        py5.vertex(0, 0, h)
        
        py5.vertex(l, 0, 0)
        py5.vertex(0, -w, 0)
        py5.vertex(0, 0, h)
        
        py5.vertex(-l, 0, 0)
        py5.vertex(0, w, 0)
        py5.vertex(0, 0, h)
        
        py5.vertex(-l, 0, 0)
        py5.vertex(0, -w, 0)
        py5.vertex(0, 0, h)
        
        # Bottom side
        py5.vertex(l, 0, 0)
        py5.vertex(0, w, 0)
        py5.vertex(0, 0, -h)
        
        py5.vertex(l, 0, 0)
        py5.vertex(0, -w, 0)
        py5.vertex(0, 0, -h)
        
        py5.vertex(-l, 0, 0)
        py5.vertex(0, w, 0)
        py5.vertex(0, 0, -h)
        
        py5.vertex(-l, 0, 0)
        py5.vertex(0, -w, 0)
        py5.vertex(0, 0, -h)
        
        py5.end_shape()
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
        import os
        os._exit(0)

py5.run_sketch()
