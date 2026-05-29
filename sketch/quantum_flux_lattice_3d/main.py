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
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global lattice_points
    lattice_points = []
    cols, rows = 30, 30
    spacing = 80
    for i in range(-cols, cols):
        for j in range(-rows, rows):
            x = i * spacing + (spacing / 2 if j % 2 == 1 else 0)
            z = j * spacing * 0.866
            if x*x + z*z < (1200*1200):
                lattice_points.append((x, z))
    lattice_points = np.array(lattice_points)

def draw():
    py5.background(10, 10, 15)
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 + 300, -500)
    
    t = py5.frame_count * 0.02
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.2)
    
    py5.no_stroke()
    
    for (x, z) in lattice_points:
        noise_val = py5.os_noise(x * 0.002, z * 0.002, t * 0.5)
        dist = np.sqrt(x*x + z*z)
        
        # Height and color modulation
        height = py5.remap(noise_val, 0, 1, 50, 600) * np.exp(-dist/1000)
        hue = (180 + noise_val * 100 + py5.sin(dist*0.005 - t*2)*20) % 360
        
        py5.push_matrix()
        py5.translate(x, 0, z)
        
        # Central glowing flux line
        py5.stroke(hue, 90, 100, 80)
        py5.stroke_weight(4)
        py5.line(0, 0, 0, 0, -height, 0)
        
        # Hexagonal casing
        py5.no_fill()
        py5.stroke(hue, 60, 60, 30)
        py5.stroke_weight(2)
        py5.translate(0, -height, 0)
        py5.rotate_x(py5.PI/2)
        
        py5.begin_shape()
        for i in range(6):
            angle = i * py5.PI / 3
            r = 15 + noise_val * 10
            py5.vertex(r * py5.cos(angle), r * py5.sin(angle))
        py5.end_shape(py5.CLOSE)
        
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
