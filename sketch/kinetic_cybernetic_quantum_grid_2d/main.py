from pathlib import Path
import shutil
import subprocess
import sys
import math
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

# Grid configuration
COLS, ROWS = 40, 40
SPACING = 80
X_OFFSET = - (COLS * SPACING) / 2
Y_OFFSET = - (ROWS * SPACING) / 2
Z_NOISE_SCALE = 0.05
TIME_SCALE = 0.01

def project_iso(x, y, z):
    # Isometric projection: rotate Z by 45 deg, X by 35.264 deg (approx 0.615 rad)
    # Simplified version for isometric view:
    # iso_x = (x - y) * cos(30)
    # iso_y = (x + y) * sin(30) - z
    # Since we want it to look good, let's use standard angles.
    cos30 = math.cos(math.radians(30))
    sin30 = math.sin(math.radians(30))
    ix = (x - y) * cos30
    iy = (x + y) * sin30 - z
    return ix, iy

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.color_mode(py5.RGB, 255)

def draw():
    py5.background(0)
    py5.translate(py5.width / 2, py5.height / 2 + 200)
    
    t = py5.frame_count * TIME_SCALE
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    py5.no_fill()
    
    py5.begin_shape(py5.LINES)
    for x in range(COLS):
        for y in range(ROWS):
            px = X_OFFSET + x * SPACING
            py = Y_OFFSET + y * SPACING
            
            noise_val = py5.os_noise(x * Z_NOISE_SCALE, y * Z_NOISE_SCALE, t)
            pz = py5.remap(noise_val, -1, 1, -200, 200)
            
            intensity_noise = py5.os_noise(x * 0.1 + t*2, y * 0.1, t * 5)
            
            if intensity_noise > 0.7:
                py5.stroke(255, 255, 255, 200)
            elif intensity_noise > 0.4:
                py5.stroke(0, 255, 255, 150)
            else:
                py5.stroke(10, 50, 150, 80)
            
            ix, iy = project_iso(px, py, pz)
            
            if x < COLS - 1:
                nx = X_OFFSET + (x + 1) * SPACING
                ny = Y_OFFSET + y * SPACING
                nz = py5.remap(py5.os_noise((x + 1) * Z_NOISE_SCALE, y * Z_NOISE_SCALE, t), -1, 1, -200, 200)
                inx, iny = project_iso(nx, ny, nz)
                py5.vertex(ix, iy)
                py5.vertex(inx, iny)
                
            if y < ROWS - 1:
                nx = px
                ny = Y_OFFSET + (y + 1) * SPACING
                nz = py5.remap(py5.os_noise(x * Z_NOISE_SCALE, (y + 1) * Z_NOISE_SCALE, t), -1, 1, -200, 200)
                inx, iny = project_iso(nx, ny, nz)
                py5.vertex(ix, iy)
                py5.vertex(inx, iny)
                
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
