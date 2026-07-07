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

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.pixel_density(1)
    py5.background(20)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.rect_mode(py5.CENTER)

def draw():
    py5.background(10, 80, 15)
    
    t_global = py5.frame_count * 0.05
    
    cols = 80
    rows = 45
    w = SIZE[0] / cols
    h = SIZE[1] / rows
    
    py5.no_stroke()
    
    # We draw a grid where time is displaced based on the X coordinate (Slit-scan effect)
    for cx in range(cols):
        # Time displacement: right side is in the "future" compared to the left side
        # A maximum time delay of 6.0 across the screen
        t_local = t_global - (cx / cols) * 6.0
        
        x = cx * w + w/2
        
        for cy in range(rows):
            y = cy * h + h/2
            
            # Complex motion for each cell based on its local time and Y position
            # We use multiple sine waves to create a chaotic but continuous flow
            
            wave1 = np.sin(t_local + cy * 0.1)
            wave2 = np.cos(t_local * 1.3 - cy * 0.2)
            
            # The rotation of the element
            rot = wave1 * py5.PI + wave2 * py5.HALF_PI
            
            # The size of the element
            sz = (0.5 + 0.5 * np.sin(t_local * 2.0 + cy * 0.1)) * w * 1.5
            
            # The color hue (cycles through the rainbow based on local time)
            hue = (t_local * 20.0 + cy * 5.0) % 360
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(rot)
            
            # Draw nested shapes to create a rich texture
            py5.fill(hue, 80, 90, 90)
            py5.rect(0, 0, sz, sz)
            
            py5.fill((hue + 180) % 360, 80, 90, 90)
            py5.rect(0, 0, sz * 0.5, sz * 0.5)
            
            py5.pop_matrix()

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
