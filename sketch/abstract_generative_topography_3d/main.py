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

cols = 80
rows = 80
scl = 40
w = cols * scl
h = rows * scl

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.02
    flying = py5.frame_count * 0.05
    
    terrain = []
    for y in range(rows):
        terrain.append([])
        for x in range(cols):
            terrain[y].append(py5.os_noise(x * 0.1, y * 0.1 - flying, t * 0.1) * 600 - 200)
    
    py5.translate(py5.width/2, py5.height/2 + 300)
    py5.rotate_x(py5.PI/2.5)
    
    py5.translate(-w/2, -h/2)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            z1 = terrain[y][x]
            z2 = terrain[y+1][x]
            
            hue1 = (200 + z1 * 0.2 + t * 20) % 360
            py5.stroke(hue1, 80, 90)
            py5.vertex(x*scl, y*scl, z1)
            
            hue2 = (200 + z2 * 0.2 + t * 20) % 360
            py5.stroke(hue2, 80, 90)
            py5.vertex(x*scl, (y+1)*scl, z2)
        py5.end_shape()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
            
        import os
        os._exit(0)

py5.run_sketch()
