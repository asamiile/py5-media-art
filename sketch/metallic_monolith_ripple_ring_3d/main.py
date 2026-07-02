from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
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
    py5.no_stroke()
    # Simple depth test for proper occlusion of monoliths
    py5.hint(py5.ENABLE_DEPTH_TEST)

def draw():
    py5.background(20, 30, 10) # Dark minimal background
    
    # Lighting
    py5.ambient_light(0, 0, 40)
    py5.directional_light(200, 10, 100, 0, 1, -1)
    py5.point_light(50, 80, 100, 0, 0, 500)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -500)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.1)
    
    num_pillars = 120
    radius = 800
    
    for i in range(num_pillars):
        angle = py5.remap(i, 0, num_pillars, 0, py5.TWO_PI)
        
        # Calculate ripple heights
        ripple1 = py5.sin(angle * 4 + t)
        ripple2 = py5.cos(angle * 8 - t * 1.5)
        n_val = py5.os_noise(i * 0.1, t * 0.5)
        
        h = 200 + (ripple1 + ripple2 + n_val) * 150
        if h < 20: h = 20
        
        x = py5.cos(angle) * radius
        y = py5.sin(angle) * radius
        
        py5.push_matrix()
        py5.translate(x, y, h / 2)
        
        # Color based on height and angle
        hue = (40 + py5.remap(h, 20, 650, 0, 60) + py5.frame_count) % 360
        py5.fill(hue, py5.remap(h, 20, 650, 40, 90), py5.remap(h, 20, 650, 50, 100))
        
        # Rotate pillar to face center
        py5.rotate_z(angle)
        
        py5.box(30, 80, h)
        py5.pop_matrix()
        
    # Inner ring
    num_inner = 60
    inner_radius = 500
    for i in range(num_inner):
        angle = py5.remap(i, 0, num_inner, 0, py5.TWO_PI)
        ripple = py5.sin(angle * 6 - t * 2)
        h = 100 + ripple * 80
        
        x = py5.cos(angle) * inner_radius
        y = py5.sin(angle) * inner_radius
        
        py5.push_matrix()
        py5.translate(x, y, h / 2)
        py5.fill((200 + py5.frame_count * 2) % 360, 80, 100)
        py5.rotate_z(angle)
        py5.box(20, 50, h)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES*100):.1f}%)")

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
            
        import os
        os._exit(0)

py5.run_sketch()
