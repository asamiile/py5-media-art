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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw_isometric_cube(x, y, w, h, d, hue):
    # Top face
    py5.fill(hue, 60, 100)
    py5.begin_shape()
    py5.vertex(x, y - d)
    py5.vertex(x + w, y - h/2 - d)
    py5.vertex(x, y - h - d)
    py5.vertex(x - w, y - h/2 - d)
    py5.end_shape(py5.CLOSE)
    
    # Left face
    py5.fill(hue, 80, 80)
    py5.begin_shape()
    py5.vertex(x - w, y - h/2 - d)
    py5.vertex(x, y - d)
    py5.vertex(x, y)
    py5.vertex(x - w, y - h/2)
    py5.end_shape(py5.CLOSE)
    
    # Right face
    py5.fill(hue, 90, 50)
    py5.begin_shape()
    py5.vertex(x, y - d)
    py5.vertex(x + w, y - h/2 - d)
    py5.vertex(x + w, y - h/2)
    py5.vertex(x, y)
    py5.end_shape(py5.CLOSE)
    
def draw():
    py5.background(280, 90, 15) # Dark neon purple background
    
    time = py5.frame_count * 0.05
    
    py5.translate(SIZE[0]/2, SIZE[1]/2 - 500)
    
    cols = 35
    rows = 35
    
    w = 60 # Half width
    h = 60 # Half height
    
    # Needs to be drawn from back to front for painters algorithm
    # Isometric sorting: (row + col) determines depth
    
    py5.no_stroke()
    #py5.stroke(280, 90, 5) # Optional: outline for retro feel
    
    for r in range(rows):
        for c in range(cols):
            # Calculate isometric x, y
            iso_x = (c - r) * w
            iso_y = (c + r) * h / 2
            
            # Use noise for building height
            # Adding time shifts the noise, creating a scrolling effect
            nx = c * 0.1 - time * 0.2
            ny = r * 0.1 - time * 0.2
            
            noise_val = py5.os_noise(nx, ny)
            
            # Threshold noise to get clear city blocks vs streets
            if noise_val < 0.4:
                depth = 10 # Street level
                hue = 280
            else:
                depth = py5.remap(noise_val, 0.4, 1.0, 50, 600)
                # Taller buildings have cyan/pink glowing tops
                hue = py5.remap(depth, 50, 600, 200, 320)
                
            draw_isometric_cube(iso_x, iso_y, w, h, depth, hue)

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
