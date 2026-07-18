from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

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

class Building:
    def __init__(self, x, w, h, layer, hue):
        self.x = x
        self.w = w
        self.h = h
        self.layer = layer
        self.hue = hue
        self.windows = np.random.rand(int(self.w/20), int(self.h/30)) > 0.4
        
    def draw(self, scroll_x):
        parallax_x = self.x - scroll_x * (1.0 - self.layer * 0.25)
        parallax_x = parallax_x % (SIZE[0] + 800) - 400
        
        y = SIZE[1]
        
        alpha = 255 - self.layer * 50
        py5.fill(10, 10, 15, alpha)
        py5.stroke(self.hue, 80, 100, alpha * 0.5)
        py5.stroke_weight(3)
        py5.rect(parallax_x, y - self.h, self.w, self.h)
        
        py5.no_stroke()
        window_w = 12
        window_h = 18
        py5.fill(self.hue, 90, 100, alpha)
        for wx in range(self.windows.shape[0]):
            for wy in range(self.windows.shape[1]):
                if self.windows[wx, wy]:
                    py5.rect(parallax_x + 15 + wx*20, y - self.h + 20 + wy*30, window_w, window_h)

buildings = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    for layer in range(4):
        for i in range(50):
            x = random.randint(0, SIZE[0] + 800)
            w = random.randint(150, 500)
            h = random.randint(300, 2000) - layer * 300
            hue = random.choice([190, 320, 280, 50])
            buildings.append(Building(x, w, max(200, h), layer, hue))
            
    buildings.sort(key=lambda b: -b.layer)
    
def draw():
    py5.background(10, 15, 20)
    
    t = py5.frame_count
    
    # Moon/Sun
    py5.no_stroke()
    py5.fill(0, 0, 100, 200)
    py5.circle(SIZE[0] * 0.8, SIZE[1] * 0.3, 400)
    
    for b in buildings:
        b.draw(t * 20)
        
    py5.load_np_pixels()
    
    if py5.frame_count % 3 == 0 and random.random() > 0.4:
        for _ in range(random.randint(1, 15)):
            y1 = random.randint(0, SIZE[1] - 100)
            h = random.randint(5, 80)
            y2 = y1 + h
            offset = random.randint(-150, 150)
            
            if offset != 0:
                py5.np_pixels[y1:y2, :, :] = np.roll(py5.np_pixels[y1:y2, :, :], offset, axis=1)
                
            if random.random() > 0.6:
                channel = random.randint(0, 2)
                # Apply color block glitch using channel assignment correctly.
                # np_pixels shape is (H, W, 4) in ARGB order usually.
                # index 1=R, 2=G, 3=B
                py5.np_pixels[y1:y2, :, channel + 1] = 255
                
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
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
