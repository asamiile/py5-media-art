from pathlib import Path
import shutil
import subprocess
import sys
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

RES = 6
COLS = SIZE[0] // RES
ROWS = SIZE[1] // RES

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 10, 15)
    
    time_val = py5.frame_count * 0.015
    
    for y in range(ROWS):
        for x in range(COLS):
            px = x * RES
            py = y * RES
            
            # Create Turing pattern look by pushing noise through a sine wave
            # The noise defines the "topography" and sine creates contour lines
            
            n1 = py5.os_noise(x * 0.01, y * 0.01, time_val * 0.5)
            n2 = py5.os_noise(x * 0.03, y * 0.03, time_val * 0.8 + 100)
            
            combined_noise = n1 + n2 * 0.5
            
            # The multiplier dictates the density of the stripes
            val = py5.sin(combined_noise * 30.0 + time_val * 2.0)
            
            if val > 0.3:
                # Color based on noise map
                hue = (180 + combined_noise * 120 + time_val * 20) % 360
                # Fade the edges of the lines
                alpha = py5.remap(val, 0.3, 1.0, 50, 255)
                py5.fill(hue, 70, 90, alpha)
                py5.circle(px + RES/2, py + RES/2, RES * 1.5)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
