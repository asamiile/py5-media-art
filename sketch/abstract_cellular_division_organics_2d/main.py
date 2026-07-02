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

RES = 20
COLS = SIZE[0] // RES
ROWS = SIZE[1] // RES

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(220, 80, 15) # Dark blue/purple background
    
    time_val = py5.frame_count * 0.03
    
    # Draw organic blobs
    py5.fill(160, 60, 90)
    
    # We will draw a bunch of circles based on noise
    # We add an offset to the noise based on distance from center to make it look like a central organism
    
    for y in range(ROWS):
        for x in range(COLS):
            px = x * RES
            py = y * RES
            
            # Distance from center
            dx = px - SIZE[0]/2
            dy = py - SIZE[1]/2
            dist = py5.sqrt(dx*dx + dy*dy)
            
            # Base noise
            n = py5.os_noise(x * 0.05, y * 0.05, time_val)
            
            # Modify noise by distance (closer to center = higher value)
            dist_factor = py5.remap(dist, 0, SIZE[1]*0.6, 1.2, -0.5)
            
            val = n + dist_factor
            
            # Threshold to create sharp, organic cellular walls
            if val > 0.6:
                hue = (140 + val * 40 + py5.frame_count * 0.5) % 360
                py5.fill(hue, 70, 90)
                # Size varies by how far past the threshold it is
                size_mult = py5.remap(val, 0.6, 1.5, 0.5, 1.5)
                py5.circle(px + RES/2, py + RES/2, RES * size_mult * 1.5)

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
