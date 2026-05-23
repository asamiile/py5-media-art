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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

COLS, ROWS = 120, 90
SCL = 20

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.02
    
    # Camera flies over the landscape
    py5.translate(py5.width / 2, py5.height / 2 + 200, -300)
    py5.rotate_x(py5.PI / 3)
    
    # Slight rotation to make the flyover more dynamic
    py5.rotate_z(py5.sin(t * 0.5) * 0.2)
    
    # Center the grid
    py5.translate(-COLS * SCL / 2, -ROWS * SCL / 2)
    
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # We draw horizontal lines to form the topographic map
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Calculate heights for current row and next row
            # The 't' parameter drives the landscape backward, giving the illusion of flying forward
            z1 = py5.noise(x * 0.1, (y - t * 10) * 0.1)
            z2 = py5.noise(x * 0.1, (y + 1 - t * 10) * 0.1)
            
            # Map noise (0-1) to elevation (-150 to +300)
            elev1 = py5.remap(z1, 0, 1, -150, 400)
            elev2 = py5.remap(z2, 0, 1, -150, 400)
            
            # Color is based on elevation (higher = warmer/brighter colors)
            hue = py5.remap(elev1, -150, 400, 180, 360) % 360
            py5.stroke(hue, 80, 100, 90)
            
            py5.vertex(x * SCL, y * SCL, elev1)
            
            hue2 = py5.remap(elev2, -150, 400, 180, 360) % 360
            py5.stroke(hue2, 80, 100, 90)
            py5.vertex(x * SCL, (y + 1) * SCL, elev2)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
