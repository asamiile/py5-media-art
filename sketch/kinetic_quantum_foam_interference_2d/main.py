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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_CENTERS = 12
CENTERS = np.random.uniform(0.1, 0.9, (NUM_CENTERS, 2))
CENTERS[:, 0] *= SIZE[0]
CENTERS[:, 1] *= SIZE[1]

FREQS = np.random.uniform(0.5, 2.0, NUM_CENTERS)
PHASES = np.random.uniform(0, py5.TWO_PI, NUM_CENTERS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(5, 0, 15)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    max_radius = 4500
    num_rings = 200
    
    for i in range(NUM_CENTERS):
        cx = CENTERS[i, 0] + np.sin(t * FREQS[i] * 0.2 + PHASES[i]) * 400
        cy = CENTERS[i, 1] + np.cos(t * FREQS[i] * 0.3 + PHASES[i]) * 400
        
        r = int(py5.remap(np.sin(i), -1, 1, 50, 200))
        g = int(py5.remap(np.cos(i), -1, 1, 50, 150))
        b = int(py5.remap(np.sin(i*2), -1, 1, 150, 255))
        
        py5.stroke(r, g, b, 40)
        
        for j in range(num_rings):
            radius = (j * (max_radius / num_rings) - t * 50 * FREQS[i]) % max_radius
            if radius > 0:
                py5.ellipse(cx, cy, radius * 2, radius * 2)

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
