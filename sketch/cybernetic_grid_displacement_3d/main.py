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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(220, 90, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -500)
    
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.1)
    
    grid_size = 80
    spacing = 40
    
    offset_x = -grid_size * spacing / 2
    offset_y = -grid_size * spacing / 2
    
    py5.translate(offset_x, offset_y, 0)
    
    noise_scale = 0.02
    z_scale = 600
    
    # Store z values to connect lines easily
    z_vals = np.zeros((grid_size, grid_size))
    
    for x in range(grid_size):
        for y in range(grid_size):
            # Animated 3D noise field
            nx = x * noise_scale
            ny = y * noise_scale
            z = py5.os_noise(nx, ny, t * 0.5) * z_scale
            
            # Attenuate edges to keep grid contained
            dx = (x - grid_size/2) / (grid_size/2)
            dy = (y - grid_size/2) / (grid_size/2)
            dist = np.sqrt(dx*dx + dy*dy)
            mask = max(0, 1 - dist)
            
            z_vals[x, y] = z * mask
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw grid lines
    for x in range(grid_size - 1):
        py5.begin_shape(py5.QUAD_STRIP)
        for y in range(grid_size):
            z1 = z_vals[x, y]
            z2 = z_vals[x+1, y]
            
            hue1 = (180 + z1 * 0.2 + t * 50) % 360
            py5.stroke(hue1, 90, 100, 60)
            py5.vertex(x * spacing, y * spacing, z1)
            
            hue2 = (180 + z2 * 0.2 + t * 50) % 360
            py5.stroke(hue2, 90, 100, 60)
            py5.vertex((x+1) * spacing, y * spacing, z2)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
