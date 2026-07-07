from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid settings
FONT_SIZE = 36
COLS = SIZE[0] // FONT_SIZE + 1
ROWS = SIZE[1] // FONT_SIZE + 1

class Stream:
    def __init__(self, col):
        self.col = col
        self.y = random.uniform(-1000, 0)
        self.speed = random.uniform(10, 30)
        self.chars = []
        self.length = random.randint(5, 25)
        for _ in range(self.length):
            self.chars.append(chr(random.randint(33, 126)))
            
    def update(self):
        self.y += self.speed
        if self.y > SIZE[1] + self.length * FONT_SIZE:
            self.y = random.uniform(-1000, 0)
            self.speed = random.uniform(10, 30)
            self.length = random.randint(5, 25)
            self.chars = [chr(random.randint(33, 126)) for _ in range(self.length)]
            
        # Randomly change some characters
        if random.random() < 0.2:
            idx = random.randint(0, self.length - 1)
            self.chars[idx] = chr(random.randint(33, 126))

streams = []

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.pixel_density(1)
    py5.background(5, 10, 5)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Try to set a monospace font, otherwise use default
    try:
        font = py5.create_font("Courier New", FONT_SIZE)
        py5.text_font(font)
    except:
        py5.text_size(FONT_SIZE)
        
    py5.text_align(py5.CENTER, py5.CENTER)
    
    # 3 streams per column for high density
    for c in range(COLS):
        for _ in range(3):
            streams.append(Stream(c))

def draw():
    # Fade background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10, 5, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.05
    
    # Check for glitch event
    glitch_intensity = 0
    if random.random() < 0.05 or (np.sin(t) > 0.95):
        glitch_intensity = random.uniform(5, 30)
        
    py5.blend_mode(py5.ADD)
    
    for stream in streams:
        stream.update()
        
        x = stream.col * FONT_SIZE + FONT_SIZE / 2
        
        for i in range(stream.length):
            char_y = stream.y - i * FONT_SIZE
            
            if char_y < 0 or char_y > SIZE[1]:
                continue
                
            char = stream.chars[i]
            
            # The leading character is brighter and whiter
            if i == 0:
                col = (200, 255, 200)
            else:
                # Fade out along the tail
                alpha = py5.remap(i, 0, stream.length, 255, 0)
                col = (0, alpha, 50) # Greenish
                
            if glitch_intensity > 0 and random.random() < 0.1:
                # Chromatic aberration glitch
                offset_x = random.uniform(-glitch_intensity, glitch_intensity)
                offset_y = random.uniform(-glitch_intensity, glitch_intensity)
                
                # Red channel
                py5.fill(255, 0, 50, 150)
                py5.text(char, x + offset_x, char_y + offset_y)
                
                # Blue channel
                py5.fill(0, 100, 255, 150)
                py5.text(char, x - offset_x, char_y - offset_y)
                
                # Draw a glitch rectangle
                py5.fill(255, 255, 255, random.uniform(50, 200))
                py5.rect(x - FONT_SIZE/2, char_y - FONT_SIZE/2, FONT_SIZE, FONT_SIZE/4)
            else:
                # Normal draw
                py5.fill(col[0], col[1], col[2])
                py5.text(char, x, char_y)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
