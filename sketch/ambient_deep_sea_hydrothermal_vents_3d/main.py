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

class Particle:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-10, -5) # Move up
        self.vz = random.uniform(-2, 2)
        self.life = 255
        self.max_life = random.uniform(150, 300)
        self.size = random.uniform(5, 15)
        # Random hue between teal, bright green, and cyan
        self.hue = random.choice([160, 180, 200]) + random.uniform(-10, 10)
        
    def update(self, frame):
        # 3D Perlin noise for turbulence
        nx = py5.os_noise(self.x * 0.005, self.y * 0.005, self.z * 0.005 + frame * 0.01) - 0.5
        ny = py5.os_noise(self.x * 0.005 + 100, self.y * 0.005, self.z * 0.005) - 0.5
        nz = py5.os_noise(self.x * 0.005 + 200, self.y * 0.005, self.z * 0.005 + frame * 0.01) - 0.5
        
        self.vx += nx * 0.5
        self.vy += ny * 0.2 # Small variation in upward movement
        self.vz += nz * 0.5
        
        # Apply drag
        self.vx *= 0.95
        self.vz *= 0.95
        
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        
        self.life -= 255 / self.max_life
        self.size += 0.1 # Expand as it rises and cools

    def draw(self):
        py5.push_matrix()
        py5.translate(self.x, self.y, self.z)
        
        alpha = max(0, self.life)
        # Shift color to cool blue/purple as it dies
        shifted_hue = self.hue + (255 - self.life) * 0.2
        py5.fill(shifted_hue % 360, 80, 100, alpha * 0.5)
        
        py5.no_stroke()
        py5.circle(0, 0, self.size)
        py5.pop_matrix()

class Vent:
    def __init__(self, x, z):
        self.x = x
        self.y = SIZE[1] * 0.8 # Base of the ocean
        self.z = z
        self.particles = []
        
    def update_and_draw(self, frame):
        # Emit new particles
        for _ in range(5):
            self.particles.append(Particle(
                self.x + random.uniform(-20, 20),
                self.y,
                self.z + random.uniform(-20, 20)
            ))
            
        # Draw rock structure for vent
        py5.push_matrix()
        py5.translate(self.x, self.y + 50, self.z)
        py5.fill(200, 20, 20, 200) # Dark rock
        py5.no_stroke()
        py5.rotate_x(py5.PI/2)
        # Very simple vent structure using a squashed sphere
        py5.scale(1, 1, 3)
        py5.sphere(80)
        py5.pop_matrix()
        
        # Update and draw particles
        for p in reversed(self.particles):
            p.update(frame)
            if p.life <= 0:
                self.particles.remove(p)
            else:
                p.draw()

vents = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.sphere_detail(20)
    
    # Create multiple vents
    for _ in range(6):
        vents.append(Vent(
            random.uniform(SIZE[0] * 0.2, SIZE[0] * 0.8),
            random.uniform(-SIZE[1] * 0.3, SIZE[1] * 0.3)
        ))

def draw():
    py5.background(220, 90, 5) # Deep ocean dark blue
    py5.blend_mode(py5.ADD)
    
    # Camera gently panning
    cam_x = SIZE[0]/2 + py5.sin(py5.frame_count * 0.002) * SIZE[0] * 0.5
    cam_z = SIZE[1] * 0.5 + py5.cos(py5.frame_count * 0.002) * SIZE[1] * 0.5
    py5.camera(cam_x, SIZE[1] * 0.5, cam_z, SIZE[0]/2, SIZE[1]*0.6, 0, 0, 1, 0)
    
    # Lighting
    py5.ambient_light(220, 80, 20)
    
    for v in vents:
        v.update_and_draw(py5.frame_count)
    
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
