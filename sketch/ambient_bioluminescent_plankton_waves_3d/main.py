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

NUM_PARTICLES = 6000

class Plankton:
    def __init__(self):
        self.x = random.uniform(-SIZE[0], SIZE[0] * 2)
        self.z = random.uniform(-SIZE[1], SIZE[1])
        self.base_y = SIZE[1] * 0.8
        self.glow = 0
        self.offset = random.uniform(0, py5.TWO_PI)
        
    def draw(self, frame):
        # Wave motion
        wave_x = self.x * 0.002
        wave_z = self.z * 0.002
        time_factor = frame * 0.02
        
        # Complex wave using noise and sine
        wave_height = py5.sin(wave_x + time_factor) * py5.cos(wave_z + time_factor * 0.8) * 150
        noise_val = py5.os_noise(self.x * 0.005, self.z * 0.005, frame * 0.01)
        
        y = self.base_y + wave_height + noise_val * 100
        
        # Bioluminescence triggers when at the peak of a wave or moving fast
        velocity_y = py5.cos(wave_x + time_factor) * py5.cos(wave_z + time_factor * 0.8) * 150 * 0.02
        
        target_glow = 0
        if y < SIZE[1] * 0.65 or abs(velocity_y) > 2.0:
            target_glow = 255
            
        # Smooth glow transition
        self.glow = py5.lerp(self.glow, target_glow, 0.1)
        
        if self.glow > 10:
            py5.push_matrix()
            py5.translate(self.x, y, self.z)
            
            # Cyan to deep blue bioluminescence
            py5.fill(190 + noise_val * 30, 80, 100, self.glow)
            py5.no_stroke()
            
            size = 2 + (self.glow / 255.0) * 4
            py5.box(size)
            
            py5.pop_matrix()

plankton_swarm = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        plankton_swarm.append(Plankton())

def draw():
    py5.background(5, 80, 10) # Very dark midnight blue/black
    py5.blend_mode(py5.ADD)
    
    # Camera setup
    py5.translate(SIZE[0]/2, SIZE[1] * 0.2, -SIZE[1] * 0.5)
    py5.rotate_x(py5.PI / 6)
    
    # Slow panning
    py5.rotate_y(py5.sin(py5.frame_count * 0.005) * 0.2)
    
    for p in plankton_swarm:
        p.draw(py5.frame_count)

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
