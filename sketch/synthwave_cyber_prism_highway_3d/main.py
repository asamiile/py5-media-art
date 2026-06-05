from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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

# Terrain settings
cols, rows = 60, 40
scl = 100
w = cols * scl
h = rows * scl


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)


def draw():
    py5.background(280, 80, 10)
    
    # Sunset
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 - 300, -2000)
    py5.no_stroke()
    
    # Draw glowing sun with scanlines
    for i in range(20, 0, -1):
        if i % 2 == 0:
            py5.fill(320 + i * 2, 80, 100)
        else:
            continue
            
        py5.ellipse(0, 0, i * 60, i * 60)
        
    py5.fill(280, 80, 10)
    # Scanline cuts
    for y in range(-600, 600, 40):
        py5.rect(-700, y + (py5.frame_count % 40), 1400, 15)
    py5.pop_matrix()

    # Move camera
    py5.translate(py5.width / 2, py5.height / 2 + 300, 300)
    py5.rotate_x(py5.PI / 3)
    py5.translate(-w / 2, -h / 2)
    
    flying = py5.frame_count * 0.1
    
    # Generate terrain heights
    terrain = np.zeros((cols, rows))
    for x in range(cols):
        for y in range(rows):
            # Flat highway in the center
            if cols/2 - 4 < x < cols/2 + 4:
                terrain[x][y] = 0
            else:
                dist_from_center = abs(x - cols/2)
                terrain[x][y] = py5.remap(py5.os_noise(x * 0.1, y * 0.1 - flying), -1, 1, -200, 200) * (dist_from_center * 0.1)

    # Draw wireframe terrain
    py5.stroke_weight(3)
    py5.no_fill()
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Depth coloring
            depth = py5.remap(y, 0, rows, 0, 100)
            hue = py5.remap(x, 0, cols, 280, 340)
            py5.stroke(hue, 100, 100, 100 - depth)
            
            # Fill for solid grid
            py5.fill(280, 90, 10, 100)
            
            py5.vertex(x * scl, y * scl, terrain[x][y])
            py5.vertex(x * scl, (y + 1) * scl, terrain[x][y + 1])
        py5.end_shape()

    # Draw floating prisms along highway
    py5.push_matrix()
    py5.translate(cols/2 * scl, 0, 0)
    
    for i in range(15):
        pz = (py5.frame_count * 20 + i * 400) % h
        py5.push_matrix()
        py5.translate(0, pz, -100 + np.sin(py5.frame_count * 0.05 + i) * 50)
        
        py5.rotate_x(py5.frame_count * 0.02 + i)
        py5.rotate_y(py5.frame_count * 0.03 + i)
        
        py5.stroke(180, 100, 100, 80)
        py5.stroke_weight(5)
        py5.fill(320, 100, 100, 40)
        py5.box(150)
        
        py5.pop_matrix()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
