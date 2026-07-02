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

COLS = 60
ROWS = 60
SCL = 60 # Scale of each grid cell
W = COLS * SCL
H = ROWS * SCL

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(240, 80, 10)
    
    # Lighting and camera
    py5.ambient_light(300, 80, 50)
    py5.directional_light(320, 100, 100, 0, 1, -1)
    py5.directional_light(200, 100, 50, -1, 0, 0)
    
    # Retro synthwave sun
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2 - 300, -2000)
    py5.no_stroke()
    py5.fill(340, 80, 100)
    py5.emissive(340, 80, 100)
    py5.circle(0, 0, 800)
    py5.pop_matrix()
    
    py5.emissive(0, 0, 0)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 300)
    py5.rotate_x(py5.PI / 2.5)
    py5.translate(-W/2, -H/2)
    
    flying = py5.frame_count * 0.05
    
    terrain = []
    for y in range(ROWS):
        terrain.append([])
        for x in range(COLS):
            # Calculate height with noise
            noise_val = py5.os_noise(x * 0.1, y * 0.1 - flying, flying * 0.2)
            height_val = py5.remap(noise_val, 0, 1, -200, 300)
            
            # Flatten out a "valley" in the middle
            dist_from_center = abs(x - COLS/2)
            valley_factor = py5.constrain(py5.remap(dist_from_center, 0, 15, 0, 1), 0, 1)
            height_val *= valley_factor
            
            terrain[y].append(height_val)
            
    # Draw wireframe grid
    py5.stroke(320, 100, 100) # Neon pink wireframe
    py5.stroke_weight(2)
    py5.fill(240, 90, 15) # Dark purple ground
    
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            py5.vertex(x * SCL, y * SCL, terrain[y][x])
            py5.vertex(x * SCL, (y+1) * SCL, terrain[y+1][x])
        py5.end_shape()

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
