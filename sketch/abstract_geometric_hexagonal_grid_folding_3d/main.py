from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math

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

HEX_RADIUS = 60
HEX_WIDTH = math.sqrt(3) * HEX_RADIUS
HEX_HEIGHT = 2 * HEX_RADIUS

COLS = int(SIZE[0] / HEX_WIDTH) + 4
ROWS = int(SIZE[1] / (HEX_HEIGHT * 0.75)) + 4

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(20)
    
    # Lighting
    py5.ambient_light(0, 0, 40)
    py5.directional_light(200, 40, 100, 0.5, 0.5, -1)
    py5.directional_light(320, 60, 80, -0.5, 0.2, -1)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 200, -500)
    py5.rotate_x(py5.PI / 3)
    
    t = py5.frame_count * 0.02
    
    py5.translate(-COLS * HEX_WIDTH / 2, -ROWS * HEX_HEIGHT * 0.75 / 2)
    
    py5.no_stroke()
    
    for row in range(ROWS):
        for col in range(COLS):
            x = col * HEX_WIDTH
            y = row * HEX_HEIGHT * 0.75
            
            # Offset odd rows
            if row % 2 == 1:
                x += HEX_WIDTH / 2
                
            # Noise values for elevation and tilting
            elevation = py5.os_noise(col * 0.1, row * 0.1, t) * 400
            tilt_x = py5.os_noise(col * 0.1 + 100, row * 0.1, t) * py5.PI / 4 - py5.PI / 8
            tilt_y = py5.os_noise(col * 0.1, row * 0.1 + 100, t) * py5.PI / 4 - py5.PI / 8
            
            py5.push_matrix()
            py5.translate(x, y, elevation)
            py5.rotate_x(tilt_x)
            py5.rotate_y(tilt_y)
            
            # Color based on elevation
            hue = py5.remap(elevation, -400, 400, 180, 280)
            py5.fill(hue, 70, 90)
            
            # Draw hexagon
            py5.begin_shape()
            for i in range(6):
                angle = py5.PI / 3 * i - py5.PI / 6
                px = py5.cos(angle) * (HEX_RADIUS * 0.9)
                py5.sin_angle = py5.sin(angle)
                py_pos = py5.sin_angle * (HEX_RADIUS * 0.9)
                py5.vertex(px, py_pos, 0)
            py5.end_shape(py5.CLOSE)
            
            py5.pop_matrix()

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
