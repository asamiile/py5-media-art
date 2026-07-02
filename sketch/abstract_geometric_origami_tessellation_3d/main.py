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
DURATION_SEC = 10
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

def draw():
    py5.background(10, 5, 10)
    py5.blend_mode(py5.BLEND)
    
    # Lighting for 3D effect
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 0.5, 0.5, -1)
    py5.point_light(200, 80, 100, py5.width/2, py5.height/2, 200)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.1)
    
    grid_w = 40
    grid_h = 40
    spacing = 30
    
    offset_x = (grid_w * spacing) / 2
    offset_y = (grid_h * spacing) / 2
    
    py5.translate(-offset_x, -offset_y, 0)
    
    py5.stroke(0, 0, 100, 50)
    py5.stroke_weight(1)
    
    for y in range(grid_h - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(grid_w):
            for dy in [0, 1]:
                cx = x * spacing
                cy = (y + dy) * spacing
                
                # Height mapped to noise and time
                noise_val = py5.os_noise(x * 0.1, (y + dy) * 0.1, t * 0.5)
                # Folding effect: sharp peaks
                z = pow(noise_val + 0.5, 3) * 80
                
                # Add a geometric ripple
                ripple = py5.sin(py5.dist(x, y + dy, grid_w/2, grid_h/2) * 0.5 - t) * 30
                z += ripple
                
                # Color based on height
                hue = (220 + z * 0.5 + t * 10) % 360
                py5.fill(hue, 80, 90)
                
                py5.vertex(cx, cy, z)
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
