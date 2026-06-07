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

class Shard:
    def __init__(self):
        self.reset()
        # Randomize phase for the implosion/explosion cycle
        self.phase = random.uniform(0, py5.TWO_PI)
        
    def reset(self):
        # Target position is the center core
        self.target_x = random.uniform(-50, 50)
        self.target_y = random.uniform(-50, 50)
        self.target_z = random.uniform(-50, 50)
        
        # Max scattered distance
        self.max_d = random.uniform(500, 1500)
        
        # Rotations
        self.rx = random.uniform(0, py5.TWO_PI)
        self.ry = random.uniform(0, py5.TWO_PI)
        self.rz = random.uniform(0, py5.TWO_PI)
        
        self.drx = random.uniform(-0.1, 0.1)
        self.dry = random.uniform(-0.1, 0.1)
        self.drz = random.uniform(-0.1, 0.1)
        
        # Color based on depth/distance
        self.hue_offset = random.uniform(0, 360)
        
        # Triangle vertices
        s = random.uniform(10, 40)
        self.v1 = (random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s/2, s/2))
        self.v2 = (random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s/2, s/2))
        self.v3 = (random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s/2, s/2))

shards = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    for _ in range(1200):
        shards.append(Shard())

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    # 0 to 1 progress for the 10-second loop
    progress = (py5.frame_count % TOTAL_FRAMES) / TOTAL_FRAMES
    
    for shard in shards:
        # A pulsing wave that goes back and forth (explosion/implosion)
        # We use a sine wave based on progress to create the cycle
        wave = math.sin(progress * py5.TWO_PI * 2 + shard.phase)
        # Map wave from [-1, 1] to [0, 1]
        t = (wave + 1) / 2
        
        # Position interpolation
        # t=0: Center, t=1: Exploded
        x = shard.target_x + (shard.max_d * t) * math.cos(shard.rx)
        y = shard.target_y + (shard.max_d * t) * math.sin(shard.ry)
        z = shard.target_z + (shard.max_d * t) * math.sin(shard.rz)
        
        shard.rx += shard.drx
        shard.ry += shard.dry
        shard.rz += shard.drz
        
        hue = (shard.hue_offset + progress * 360) % 360
        alpha = py5.remap(t, 0, 1, 255, 20) # Fade out as they explode
        
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.rotate_x(shard.rx)
        py5.rotate_y(shard.ry)
        py5.rotate_z(shard.rz)
        
        py5.fill(hue, 90, 100, alpha * 0.5)
        py5.begin_shape(py5.TRIANGLES)
        py5.vertex(*shard.v1)
        py5.vertex(*shard.v2)
        py5.vertex(*shard.v3)
        py5.end_shape()
        
        # White highlight for glass reflection
        py5.fill(0, 0, 100, alpha * 0.8)
        s_small = 0.5
        py5.begin_shape(py5.TRIANGLES)
        py5.vertex(shard.v1[0]*s_small, shard.v1[1]*s_small, shard.v1[2]*s_small)
        py5.vertex(shard.v2[0]*s_small, shard.v2[1]*s_small, shard.v2[2]*s_small)
        py5.vertex(shard.v3[0]*s_small, shard.v3[1]*s_small, shard.v3[2]*s_small)
        py5.end_shape()
        
        py5.pop_matrix()
        
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
