from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

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

NUM_POINTS_PER_FRAME = 8000

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 10)

def draw():
    # Very slow fade to allow cloud build up but not completely infinite
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 5)
    py5.push_matrix()
    py5.translate(0, 0, -1000)
    py5.rect(-SIZE[0], -SIZE[1], SIZE[0]*3, SIZE[1]*3)
    py5.pop_matrix()
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    time_val = py5.frame_count * 0.01
    
    py5.rotate_y(time_val * 0.5)
    py5.rotate_x(time_val * 0.3)
    py5.rotate_z(time_val * 0.2)
    
    py5.stroke_weight(2)
    
    # Generate point cloud
    for _ in range(NUM_POINTS_PER_FRAME):
        # Random spherical coords
        theta = random.uniform(0, py5.TWO_PI)
        phi = random.uniform(0, py5.PI)
        
        # Base radius sphere
        base_r = SIZE[1] * 0.4
        
        # Calculate cartesian just for noise sampling
        nx = py5.sin(phi) * py5.cos(theta)
        ny = py5.sin(phi) * py5.sin(theta)
        nz = py5.cos(phi)
        
        # Use noise to determine density/probability
        n = py5.os_noise(nx * 2, ny * 2, nz * 2 + time_val)
        
        # Only draw if probability threshold met, creating cloud shapes
        if random.random() < n * n * 2: # Squaring makes it more localized
            # Modulate radius
            r = base_r * py5.remap(n, 0, 1, 0.5, 1.5)
            
            x = nx * r
            y = ny * r
            z = nz * r
            
            hue = (200 + n * 100 + time_val * 20) % 360
            
            py5.stroke(hue, 80, 100, 15)
            py5.point(x, y, z)

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
