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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols, rows = 0, 0
scl = 80
w = 6000
h = 4000
terrain = []
flying = 0

stars = np.random.rand(500, 3)

def setup():
    global cols, rows, terrain
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cols = w // scl
    rows = h // scl
    terrain = np.zeros((cols, rows))

def draw():
    global flying, terrain
    
    flying -= 0.05 # Speed of forward movement
    
    yoff = flying
    for y in range(rows):
        xoff = 0
        for x in range(cols):
            terrain[x][y] = py5.remap(py5.os_noise(xoff, yoff), -1, 1, -400, 400)
            xoff += 0.1
        yoff += 0.1

    py5.background(250, 90, 5) # Deep purple space
    
    # Draw stars
    py5.push_matrix()
    py5.translate(0, 0, -1000)
    py5.no_stroke()
    py5.fill(0, 0, 100, 80)
    for s in stars:
        sx = py5.remap(s[0], 0, 1, 0, py5.width)
        sy = py5.remap(s[1], 0, 1, 0, py5.height / 2)
        sz = py5.remap(s[2], 0, 1, -500, 500)
        py5.circle(sx, sy, 3 + s[2] * 5)
    py5.pop_matrix()
    
    # Draw synthwave sun
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 - 200, -800)
    py5.no_stroke()
    
    # Glow effect
    for r in range(800, 0, -40):
        py5.fill(330, 80, 100, 2)
        py5.circle(0, 0, r)
    
    # Sun body
    py5.fill(340, 80, 100, 100)
    py5.circle(0, 0, 600)
    
    # Sun scanlines
    py5.fill(250, 90, 5, 100)
    for i in range(-300, 300, 40):
        offset = (py5.frame_count * 2.0) % 40
        y_pos = i + offset
        if y_pos > -300 and y_pos < 300:
            thickness = py5.remap(y_pos, -300, 300, 2, 20)
            py5.rect(-300, y_pos, 600, thickness)
    py5.pop_matrix()

    # Setup camera and perspective for terrain
    py5.translate(py5.width / 2, py5.height / 2 + 300)
    py5.rotate_x(py5.PI / 2.5)
    py5.translate(-w / 2, -h / 2 + 500)

    # Draw terrain grid
    py5.stroke_weight(4)
    py5.fill(280, 100, 15, 90)    # Dark purple terrain fill
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            dist_to_center = py5.dist(x * scl, y * scl, w/2, h/2)
            glow_alpha = py5.remap(dist_to_center, 0, w/2, 100, 0)
            
            # Cyan grid in the distance, Hot Pink up close
            hue = py5.remap(y, 0, rows, 180, 320)
            py5.stroke(hue, 100, 100, glow_alpha)
            
            py5.vertex(x * scl, y * scl, terrain[x][y])
            py5.vertex(x * scl, (y + 1) * scl, terrain[x][y + 1])
        py5.end_shape()

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
