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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)

def draw():
    py5.background(10, 80, 5)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -200)
    py5.rotate_x(py5.PI / 4)
    
    t = py5.frame_count * 0.02
    py5.rotate_z(t * 0.5)
    
    num_tentacles = 400
    segments = 30
    
    for i in range(num_tentacles):
        # Initial position on a hemisphere
        phi = py5.acos(1 - 2 * ((i + 0.5) / num_tentacles)) * 0.5  # Only top hemisphere
        theta = py5.PI * (1 + 5**0.5) * i
        
        base_x = py5.sin(phi) * py5.cos(theta) * 150
        base_y = py5.sin(phi) * py5.sin(theta) * 150
        base_z = py5.cos(phi) * 150
        
        py5.begin_shape(py5.LINE_STRIP)
        py5.stroke_weight(4)
        
        cx, cy, cz = base_x, base_y, base_z
        
        # Color based on position and time
        hue = (180 + py5.sin(phi * 2 + t) * 60) % 360
        if i % 10 == 0:
            py5.stroke((hue + 120) % 360, 90, 100, 80) # Occasional bright pink/magenta
            py5.stroke_weight(8)
        else:
            py5.stroke(hue, 90, 80, 50)
            
        for s in range(segments):
            py5.vertex(cx, cy, cz)
            
            # Flow field driven by 4D noise (x, y, z, t)
            nx = py5.os_noise(cx * 0.005, cy * 0.005, cz * 0.005, t) - 0.5
            ny = py5.os_noise(cx * 0.005 + 100, cy * 0.005, cz * 0.005, t) - 0.5
            nz = py5.os_noise(cx * 0.005 + 200, cy * 0.005, cz * 0.005, t) - 0.2 # Bias upwards
            
            # Calculate normal vector to push tentacle outwards
            dist = py5.dist(0, 0, 0, cx, cy, cz)
            norm_x = cx / dist
            norm_y = cy / dist
            norm_z = cz / dist
            
            cx += nx * 40 + norm_x * 10
            cy += ny * 40 + norm_y * 10
            cz += nz * 40 + norm_z * 10
            
        py5.end_shape()


    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
