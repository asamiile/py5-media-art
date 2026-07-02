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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols = 0
rows = 0
scl = 80
w = 4000
h = 3000

def setup():
    global cols, rows
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    cols = w // scl
    rows = h // scl

def draw():
    py5.background(270, 80, 10)
    
    t = py5.frame_count * 0.05
    flying = py5.frame_count * 0.15
    
    # Draw synthwave sun
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 - 400, -1000)
    py5.no_stroke()
    py5.fill(330, 90, 100)
    py5.circle(0, 0, 1500)
    # Sun scanlines
    py5.fill(270, 80, 10)
    for i in range(-750, 750, 40):
        py5.rect(-800, i + (t * 20) % 40, 1600, 10)
    py5.pop_matrix()
    
    # Draw terrain
    py5.translate(py5.width / 2, py5.height / 2 + 200, 0)
    py5.rotate_x(py5.PI / 2.5)
    py5.translate(-w / 2, -h / 2, 0)
    
    py5.stroke(300, 100, 100)
    py5.stroke_weight(3)
    py5.fill(270, 80, 10, 80)
    
    terrain = []
    yoff = flying
    for y in range(rows):
        row = []
        xoff = 0
        for x in range(cols):
            # Noise-based elevation
            z = py5.os_noise(xoff, yoff)
            row.append(z * 600 - 300)
            xoff += 0.1
        terrain.append(row)
        yoff += 0.1

    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            z1 = terrain[y][x]
            z2 = terrain[y + 1][x]
            
            # Map hue based on z elevation
            hue1 = py5.remap(z1, -300, 300, 260, 340)
            hue2 = py5.remap(z2, -300, 300, 260, 340)
            
            py5.stroke(hue1, 100, 100)
            py5.vertex(x * scl, y * scl, z1)
            py5.stroke(hue2, 100, 100)
            py5.vertex(x * scl, (y + 1) * scl, z2)
        py5.end_shape()


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
            
        import os
        os._exit(0)

py5.run_sketch()
