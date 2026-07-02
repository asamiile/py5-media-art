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

NUM_EMITTERS = 6
NUM_RINGS = 60

class Emitter:
    def __init__(self, id):
        self.id = id
        self.base_x = SIZE[0]/2
        self.base_y = SIZE[1]/2
        self.hue = (id * (360 / NUM_EMITTERS)) % 360
        self.radius_offset = id * 10
        
    def get_pos(self, time_val):
        # Complex orbit
        angle = time_val * 0.5 + self.id * py5.TWO_PI / NUM_EMITTERS
        radius = py5.sin(time_val * 0.2 + self.id) * SIZE[1] * 0.3
        
        x = self.base_x + py5.cos(angle) * radius
        y = self.base_y + py5.sin(angle * 1.5) * radius
        return x, y

emitters = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for i in range(NUM_EMITTERS):
        emitters.append(Emitter(i))

def draw():
    py5.background(0, 0, 5) # Dark background
    py5.blend_mode(py5.ADD)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    time_val = py5.frame_count * 0.02
    
    for e in emitters:
        ex, ey = e.get_pos(time_val)
        
        # Radiating rings
        for r in range(NUM_RINGS):
            # Distance from center increases over time to simulate waves moving outward
            wave_phase = (r * 30 - py5.frame_count * 5) % (NUM_RINGS * 30)
            if wave_phase < 0: wave_phase += NUM_RINGS * 30
            
            # Rings fade out as they get larger
            alpha = py5.remap(wave_phase, 0, NUM_RINGS * 30, 150, 0)
            
            py5.stroke(e.hue, 80, 100, alpha)
            py5.circle(ex, ey, wave_phase * 2) # Diameter

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
