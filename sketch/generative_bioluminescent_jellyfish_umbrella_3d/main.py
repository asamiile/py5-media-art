from pathlib import Path
import shutil
import subprocess
import sys
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

NUM_TENTACLES = 40
TENTACLE_LENGTH = 100

class Tentacle:
    def __init__(self, index):
        self.index = index
        self.angle = py5.TWO_PI / NUM_TENTACLES * index
        self.radius_offset = 0.5
        self.history = []
        for _ in range(TENTACLE_LENGTH):
            self.history.append((0, 0, 0))
            
    def update(self, bell_x, bell_y, bell_z, bell_radius, frame):
        # Base of tentacle attached to the bell
        tx = bell_x + py5.cos(self.angle) * bell_radius * self.radius_offset
        tz = bell_z + py5.sin(self.angle) * bell_radius * self.radius_offset
        ty = bell_y
        
        self.history.insert(0, (tx, ty, tz))
        self.history.pop()
        
    def draw(self, frame):
        py5.no_fill()
        py5.stroke(180 + (self.index % 5) * 10, 80, 100, 150)
        py5.stroke_weight(3)
        
        py5.begin_shape()
        for i in range(TENTACLE_LENGTH):
            hx, hy, hz = self.history[i]
            
            # Apply organic waving noise to trailing points
            if i > 0:
                noise_x = py5.os_noise(hx * 0.01, hy * 0.01, frame * 0.01) - 0.5
                noise_z = py5.os_noise(hx * 0.01 + 100, hy * 0.01, frame * 0.01) - 0.5
                hx += noise_x * i * 2
                hz += noise_z * i * 2
                # Slow down falling to simulate water drag
                hy -= i * 1.5
                
            py5.vertex(hx, hy, hz)
        py5.end_shape()

tentacles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for i in range(NUM_TENTACLES):
        tentacles.append(Tentacle(i))

def draw():
    py5.background(220, 90, 10) # Deep sea blue/black
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Camera gently swaying
    py5.rotate_x(py5.sin(py5.frame_count * 0.005) * 0.2 + py5.PI/8)
    py5.rotate_y(py5.frame_count * 0.005)
    
    # Rhythmic pulsing of the jellyfish
    pulse = py5.sin(py5.frame_count * 0.05)
    swim_y = py5.frame_count * -2 % (SIZE[1] * 2) + SIZE[1] # Swimming upwards loop
    
    bell_y = SIZE[1] * 0.2 + py5.sin(py5.frame_count * 0.05) * 50
    bell_radius = SIZE[1] * 0.2 + pulse * SIZE[1] * 0.05
    
    py5.push_matrix()
    py5.translate(0, bell_y, 0)
    
    # Draw Jellyfish Bell (Hemisphere)
    py5.no_stroke()
    py5.fill(190, 60, 100, 80)
    
    detail = 40
    py5.begin_shape(py5.TRIANGLE_FAN)
    py5.vertex(0, -bell_radius * 0.8, 0) # Top pole
    for i in range(detail + 1):
        angle = py5.remap(i, 0, detail, 0, py5.TWO_PI)
        # Undulating rim
        r = bell_radius + py5.sin(angle * 8 + py5.frame_count * 0.1) * 20
        vx = py5.cos(angle) * r
        vz = py5.sin(angle) * r
        vy = py5.sin(pulse) * 30 # Rim goes up and down
        py5.vertex(vx, vy, vz)
    py5.end_shape()
    
    # Inner glowing core
    py5.fill(210, 80, 100, 200)
    py5.sphere_detail(16)
    py5.sphere(bell_radius * 0.3)
    py5.pop_matrix()
    
    # Draw Tentacles
    for t in tentacles:
        t.update(0, bell_y, 0, bell_radius, py5.frame_count)
        t.draw(py5.frame_count)

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
