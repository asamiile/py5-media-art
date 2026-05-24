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
DURATION_SEC = 15  # Adjust between 10–30 seconds depending on content
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Terrain parameters
COLS = 120
ROWS = 120
SCL = 30
W = 3600
H = 3600

flying = 0.0

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    global flying
    flying -= 0.02
    
    py5.background(0)
    py5.translate(py5.width / 2, py5.height / 2 + 300)
    py5.rotate_x(py5.PI / 2.5)
    py5.translate(-W / 2, -H / 2)
    
    yoff = flying
    for y in range(ROWS - 1):
        xoff = 0
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            z1 = py5.remap(py5.noise(xoff, yoff), 0, 1, -200, 300)
            z2 = py5.remap(py5.noise(xoff, yoff + 0.1), 0, 1, -200, 300)
            
            hue1 = py5.remap(z1, -200, 300, 200, 320)
            py5.stroke(hue1, 90, 100)
            py5.fill(0, 0, 0, 200)
            py5.vertex(x * SCL, y * SCL, z1)
            
            hue2 = py5.remap(z2, -200, 300, 200, 320)
            py5.stroke(hue2, 90, 100)
            py5.fill(0, 0, 0, 200)
            py5.vertex(x * SCL, (y + 1) * SCL, z2)
            
            xoff += 0.1
        py5.end_shape()
        yoff += 0.1

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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


py5.run_sketch()
