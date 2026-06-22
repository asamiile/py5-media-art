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

NUM_PARTICLES = 1500
WELL_RADIUS = 300

class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        # Start inside the well
        r = random.uniform(0, WELL_RADIUS * 0.9)
        theta = random.uniform(0, py5.PI * 2)
        phi = random.uniform(0, py5.PI)
        
        self.x = r * math.sin(phi) * math.cos(theta)
        self.y = r * math.sin(phi) * math.sin(theta)
        self.z = r * math.cos(phi)
        
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-10, 10)
        self.vz = random.uniform(-10, 10)
        
        self.tunneling = False
        self.history = []
        self.hue = random.choice([200, 220, 280, 160])
        self.life = 0
        
    def update(self):
        self.life += 1
        
        if not self.tunneling:
            # Bounce around inside the well
            self.x += self.vx
            self.y += self.vy
            self.z += self.vz
            
            d = math.sqrt(self.x**2 + self.y**2 + self.z**2)
            if d > WELL_RADIUS:
                # Tunneling probability
                if random.random() < 0.02:
                    self.tunneling = True
                    # Shoot out with high velocity
                    speed = random.uniform(20, 40)
                    self.vx = (self.x / d) * speed
                    self.vy = (self.y / d) * speed
                    self.vz = (self.z / d) * speed
                else:
                    # Bounce back
                    n_x = self.x / d
                    n_y = self.y / d
                    n_z = self.z / d
                    
                    dot = self.vx * n_x + self.vy * n_y + self.vz * n_z
                    self.vx -= 2 * dot * n_x
                    self.vy -= 2 * dot * n_y
                    self.vz -= 2 * dot * n_z
                    
                    self.x += self.vx
                    self.y += self.vy
                    self.z += self.vz
        else:
            self.history.append((self.x, self.y, self.z))
            if len(self.history) > 20:
                self.history.pop(0)
                
            self.x += self.vx
            self.y += self.vy
            self.z += self.vz
            
            # Reset if too far
            if math.sqrt(self.x**2 + self.y**2 + self.z**2) > SIZE[0] * 2:
                self.reset()
                
    def draw(self):
        if self.tunneling:
            if len(self.history) > 1:
                py5.stroke(self.hue, 80, 100, 200)
                py5.stroke_weight(4)
                py5.no_fill()
                py5.begin_shape()
                for px, py_pos, pz in self.history:
                    py5.vertex(px, py_pos, pz)
                py5.vertex(self.x, self.y, self.z)
                py5.end_shape()
                
            py5.push_matrix()
            py5.translate(self.x, self.y, self.z)
            py5.no_stroke()
            py5.fill(self.hue, 50, 100, 255)
            py5.sphere(6)
            py5.pop_matrix()
        else:
            py5.push_matrix()
            py5.translate(self.x, self.y, self.z)
            py5.no_stroke()
            py5.fill(self.hue, 80, 80, 150)
            py5.sphere(3)
            py5.pop_matrix()

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.ADD)
    py5.sphere_detail(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    py5.background(10, 15, 20)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    t = py5.frame_count
    py5.rotate_y(t * 0.005)
    py5.rotate_x(t * 0.003)
    
    # Draw potential well
    py5.push_matrix()
    py5.no_fill()
    py5.stroke(240, 80, 100, 40)
    py5.stroke_weight(2)
    py5.sphere_detail(24)
    py5.sphere(WELL_RADIUS)
    py5.sphere_detail(8) # Reset for particles
    py5.pop_matrix()
    
    # Lighting
    py5.ambient_light(0, 0, 20)
    py5.point_light(200, 60, 100, 0, 0, 0)
    
    for p in particles:
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
