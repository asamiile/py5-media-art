from pathlib import Path
import shutil
import subprocess
import sys
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

# Bauhaus color palette: Red, Blue, Yellow, Black, White
# In HSB:
# Red: 0, 80, 90
# Blue: 220, 80, 90
# Yellow: 50, 90, 100
# Black: 0, 0, 15
# White: 0, 0, 95
colors = [
    (0, 80, 90),
    (220, 80, 90),
    (50, 90, 100),
    (0, 0, 15),
    (0, 0, 95)
]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(40, 10, 95) # Warm off-white
    
    time = py5.frame_count * 0.02
    
    cols = 12
    rows = 7
    w = SIZE[0] / cols
    h = SIZE[1] / rows
    
    py5.no_stroke()
    
    # We will use difference blending to get intersecting forms
    py5.blend_mode(py5.BLEND)
    
    for i in range(cols):
        for j in range(rows):
            py5.push_matrix()
            py5.translate(i * w + w/2, j * h + h/2)
            
            # Noise-driven animation
            n = py5.os_noise(i * 0.2, j * 0.2, time * 0.5)
            n2 = py5.os_noise(i * 0.2, j * 0.2, time * 0.5 + 100)
            
            # Select color based on coordinates
            c_idx = (i * 3 + j * 7) % len(colors)
            py5.fill(*colors[c_idx])
            
            # Scale shifts between 0.2 and 1.2
            s = py5.remap(n, 0, 1, 0.2, 1.5)
            py5.scale(s)
            
            # Rotation
            angle = n2 * py5.TWO_PI * 2
            py5.rotate(angle)
            
            shape_type = (i + j) % 4
            
            if shape_type == 0:
                py5.ellipse(0, 0, w, h)
            elif shape_type == 1:
                py5.rect(-w/2, -h/2, w, h)
            elif shape_type == 2:
                py5.triangle(-w/2, h/2, w/2, h/2, 0, -h/2)
            elif shape_type == 3:
                py5.arc(0, 0, w, h, 0, py5.PI)
                
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
