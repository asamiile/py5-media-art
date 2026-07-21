from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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

COLS = 130
ROWS = 100
SCL = 45

# Orthographic projection parameters
ANGLE_X = np.pi / 2.5 # ~72 degrees
COS_X = np.cos(ANGLE_X)
SIN_X = np.sin(ANGLE_X)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 5, 25)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    # Generate terrain Z values
    # We move "forward" by shifting the Y offset
    flying_speed = time * 2.0
    
    py5.translate(SIZE[0] / 2, SIZE[1] * 0.2) # Center horizontally, start near top vertically
    
    py5.stroke_weight(2.0)
    
    # We draw row by row, from back (ROWS) to front (0) so closer things draw on top
    # Actually since it's just lines, and we use ADD blend mode, drawing order matters less,
    # but we can fill the polygons with black to hide the back!
    py5.blend_mode(py5.BLEND)
    
    for y in range(ROWS - 1, -1, -1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Coordinates in 3D
            rx1 = (x - COLS / 2) * SCL
            ry1 = y * SCL
            
            rx2 = (x - COLS / 2) * SCL
            ry2 = (y + 1) * SCL
            
            # Noise Z
            n1 = py5.os_noise(rx1 * 0.003, (ry1 - flying_speed * SCL) * 0.003, time * 0.1)
            n2 = py5.os_noise(rx2 * 0.003, (ry2 - flying_speed * SCL) * 0.003, time * 0.1)
            
            # Map noise to height, make a valley in the middle
            valley1 = np.abs((x - COLS/2) / (COLS/2)) # 0 at center, 1 at edges
            valley2 = np.abs((x - COLS/2) / (COLS/2))
            
            z1 = py5.remap(n1, -1, 1, -200, 400) * (valley1 ** 1.5)
            z2 = py5.remap(n2, -1, 1, -200, 400) * (valley2 ** 1.5)
            
            # Project to 2D
            px1 = rx1
            py_1 = ry1 * COS_X - z1 * SIN_X
            
            px2 = rx2
            py_2 = ry2 * COS_X - z2 * SIN_X
            
            # Color based on height and distance
            alpha1 = py5.remap(y, ROWS, 0, 0, 255)
            
            # Synthwave color mapping: Low = Pink, High = Cyan
            color_factor1 = py5.constrain(py5.remap(z1, 0, 300, 0, 1), 0, 1)
            
            r1 = py5.lerp(255, 0, color_factor1)
            g1 = py5.lerp(50, 255, color_factor1)
            b1 = py5.lerp(200, 255, color_factor1)
            
            py5.fill(10, 5, 25, 255) # Opaque background color to hide terrain behind
            py5.stroke(r1, g1, b1, alpha1)
            
            py5.vertex(px1, py_1)
            py5.vertex(px2, py_2)
            
        py5.end_shape()
        
    # Draw a glowing sun in the background
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    for i in range(20, 0, -1):
        py5.fill(255, 100, 50, 10 + i * 2)
        py5.circle(0, 0, 400 + i * 20)

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
