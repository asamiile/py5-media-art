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

CHARSET = [chr(i) for i in range(0x30A0, 0x30FF)] + [str(i) for i in range(10)]

class Drop:
    def __init__(self, x, z_layer):
        self.x = x
        self.y = random.uniform(-1000, SIZE[1])
        self.z_layer = z_layer
        self.speed = py5.remap(self.z_layer, 0, 1, 8, 40)
        self.length = int(random.uniform(10, 40))
        self.chars = [random.choice(CHARSET) for _ in range(self.length)]
        
    def update(self):
        self.y += self.speed
        if self.y - self.length * 40 * py5.remap(self.z_layer, 0, 1, 0.5, 3.0) > SIZE[1]:
            self.y = random.uniform(-800, -200)
            self.x = random.uniform(0, SIZE[0])
            self.chars = [random.choice(CHARSET) for _ in range(self.length)]
            
        if random.random() > 0.7:
            self.chars[random.randint(0, self.length - 1)] = random.choice(CHARSET)

drops = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(400):
        drops.append(Drop(random.uniform(0, SIZE[0]), random.uniform(0.1, 1.0)))
        
    drops.sort(key=lambda d: d.z_layer)
    
    py5.text_align(py5.CENTER, py5.CENTER)

def draw():
    py5.background(5, 10, 5) 
    py5.no_stroke()
    
    t = py5.frame_count * 0.05
    
    for drop in drops:
        drop.update()
        
        scale_fac = py5.remap(drop.z_layer, 0, 1, 0.5, 3.0)
        base_alpha = int(py5.remap(drop.z_layer, 0, 1, 20, 255))
        
        py5.push_matrix()
        py5.translate(drop.x, drop.y)
        py5.scale(scale_fac)
        
        for i, char in enumerate(drop.chars):
            char_y = -i * 24 
            
            is_head = (i == 0)
            is_glitch = random.random() > 0.995
            
            if is_glitch:
                py5.fill(255, 50, 50, base_alpha)
                py5.text(char, -3, char_y)
                py5.fill(50, 50, 255, base_alpha)
                py5.text(char, 3, char_y)
                py5.fill(255, 255, 255, base_alpha)
            else:
                if is_head:
                    py5.fill(200, 255, 255, base_alpha)
                else:
                    tail_fade = max(0, 255 - i * (255 / drop.length))
                    py5.fill(0, tail_fade, int(tail_fade * 0.3), int((tail_fade / 255.0) * base_alpha))
            
            py5.text(char, 0, char_y)
            
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
