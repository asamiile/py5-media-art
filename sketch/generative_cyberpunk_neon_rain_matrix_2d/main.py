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

class Drop:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.reset()
        self.y = random.uniform(0, h) # Start anywhere initially

    def reset(self):
        self.x = random.uniform(0, self.w)
        self.y = random.uniform(-100, -10)
        self.z = random.uniform(0, 20) # Depth
        self.len = py5.remap(self.z, 0, 20, 10, 40)
        self.yspeed = py5.remap(self.z, 0, 20, 4, 15)
        # Cyberpunk colors: Cyan, Magenta, Neon Blue
        self.hue = random.choice([190, 320, 280])

    def fall(self, t):
        # Noise-based glitching
        glitch_chance = py5.os_noise(self.x * 0.01, self.y * 0.01, t * 5.0)
        
        glitch_offset = 0
        if glitch_chance > 0.7:
            glitch_offset = random.uniform(-20, 20)
            
        self.y += self.yspeed
        
        # Reset at bottom
        if self.y > self.h:
            self.reset()
            
        return glitch_offset

NUM_DROPS = 1500
drops = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    
    for _ in range(NUM_DROPS):
        drops.append(Drop(py5.width, py5.height))

def draw():
    # Matrix fade effect
    py5.fill(240, 90, 5, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.01
    
    for d in drops:
        offset = d.fall(t)
        
        # Draw line segment based on z-depth
        thick = py5.remap(d.z, 0, 20, 1, 4)
        
        # Glitch color
        h = d.hue
        if offset != 0:
            h = (h + 180) % 360 # Invert color on glitch
            
        # Glowing trail
        py5.fill(h, 90, 100, 200)
        py5.rect(d.x + offset, d.y, thick, d.len)
        
        # Bright head
        py5.fill(0, 0, 100, 255)
        py5.rect(d.x + offset, d.y + d.len - thick, thick, thick)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
