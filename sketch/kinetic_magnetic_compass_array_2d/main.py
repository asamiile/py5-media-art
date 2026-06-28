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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    py5.no_stroke()
    # Note: py5.smooth() is intentionally omitted as default renderer is smooth by default

def draw():
    py5.background(220, 80, 10)
    
    t = py5.frame_count * 0.015
    
    grid_size_x = 90
    grid_size_y = 50
    spacing = 40
    
    py5.translate(py5.width/2.0 - grid_size_x * spacing / 2.0, 
                  py5.height/2.0 - grid_size_y * spacing / 2.0)
    
    for x in range(grid_size_x):
        for y in range(grid_size_y):
            nx = x * 0.05
            ny = y * 0.05
            
            noise_val = py5.os_noise(nx, ny, t)
            angle = py5.remap(noise_val, 0, 1, 0, py5.TWO_PI * 2)
            
            px = x * spacing
            py_pos = y * spacing
            
            py5.push_matrix()
            py5.translate(px, py_pos)
            
            # Compass rotation
            py5.rotate(angle)
            
            # Color based on angle magnitude
            hue = py5.remap(noise_val, 0, 1, 150, 320)
            
            # Draw needle
            py5.fill(hue, 90, 100)
            py5.triangle(-6, -20, 6, -20, 0, 20)
            
            # Draw needle shadow/back
            py5.fill(hue, 90, 30)
            py5.triangle(-6, -20, 6, -20, 0, -35)
            
            # Draw center dot
            py5.fill(0, 0, 100, 50)
            py5.circle(0, -20, 6)
            
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
