import math
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Block:
    def __init__(self, x, y, z, w, h, d, axis, speed, offset, travel):
        self.base_x = x
        self.base_y = y
        self.base_z = z
        self.w = w
        self.h = h
        self.d = d
        self.axis = axis # 0: x, 1: y, 2: z
        self.speed = speed
        self.offset = offset
        self.travel = travel

blocks = []

def setup():
    global blocks
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    random.seed(42) # Deterministic structure but varied movement
    
    # Generate brutalist blocks
    # A massive central core
    blocks.append(Block(0, 0, 0, 300, 800, 300, 1, 0, 0, 0))
    
    # Add cantilevered sections
    for i in range(40):
        # Pick random dimensions for thick concrete slabs
        bw = random.choice([200, 400, 600])
        bh = random.choice([40, 80, 120])
        bd = random.choice([200, 400, 600])
        
        # Position them around the core
        bx = random.randint(-200, 200)
        by = random.randint(-300, 300)
        bz = random.randint(-200, 200)
        
        # Axis of motion
        axis = random.choice([0, 1, 2])
        if axis == 1:
            axis = 0 # Favor horizontal sliding over vertical for cantilever look
            
        speed = random.uniform(0.5, 2.0)
        offset = random.uniform(0, math.pi * 2)
        travel = random.choice([100, 200, 300])
        
        blocks.append(Block(bx, by, bz, bw, bh, bd, axis, speed, offset, travel))

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

def draw():
    py5.background(0) # Pitch black
    
    # Harsh, dramatic lighting
    py5.ambient_light(42, 40, 38) # Deep charcoal ambient
    py5.directional_light(255, 250, 240, 0.5, 0.8, -1) # Strong overhead/side white light
    py5.directional_light(100, 95, 90, -1, 0.2, 0.5) # Secondary fill
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    # Slow cinematic camera rotation
    cam_angle = (py5.frame_count / TOTAL_FRAMES) * math.pi / 2
    py5.rotate_y(cam_angle - math.pi / 4)
    py5.rotate_x(-0.2)
    
    py5.no_stroke()
    py5.fill(139, 133, 122) # Warm concrete grey
    
    t = py5.frame_count / TOTAL_FRAMES
    
    for b in blocks:
        py5.push_matrix()
        
        # Calculate sliding motion
        # We want a smooth sliding that pauses at the ends.
        # Sine wave with easing applied
        phase = (math.sin(t * math.pi * 2 * b.speed + b.offset) + 1) / 2
        slide = ease_in_out_cubic(phase) * b.travel - (b.travel / 2)
        
        tx = b.base_x
        ty = b.base_y
        tz = b.base_z
        
        if b.axis == 0:
            tx += slide
        elif b.axis == 1:
            ty += slide
        else:
            tz += slide
            
        py5.translate(tx, ty, tz)
        py5.box(b.w, b.h, b.d)
        py5.pop_matrix()

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
