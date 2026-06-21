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
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_radial_lines(num_lines, radius, color):
    py5.stroke(*color)
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for i in range(num_lines):
        angle = (i / num_lines) * py5.TWO_PI
        py5.vertex(0, 0)
        py5.vertex(radius * py5.cos(angle), radius * py5.sin(angle))
    py5.end_shape()

def draw_grid_lines(num_lines, size, color):
    py5.stroke(*color)
    py5.stroke_weight(2)
    spacing = size / num_lines
    py5.begin_shape(py5.LINES)
    # Vertical lines
    for i in range(num_lines):
        x = -size/2 + i * spacing
        py5.vertex(x, -size/2)
        py5.vertex(x, size/2)
    py5.end_shape()

def draw():
    py5.background(10)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2)
    
    num = 400
    r = 3000
    
    # Layer 1 - Radial static
    py5.push_matrix()
    draw_radial_lines(num, r, (200, 80, 80, 50))
    py5.pop_matrix()
    
    # Layer 2 - Radial rotating
    py5.push_matrix()
    py5.rotate(py5.sin(t*0.5) * 0.2)
    draw_radial_lines(num, r, (300, 80, 80, 50))
    py5.pop_matrix()
    
    # Layer 3 - Grid slow rotating
    py5.push_matrix()
    py5.rotate(t * 0.1)
    draw_grid_lines(500, r, (150, 80, 80, 40))
    py5.pop_matrix()
    
    # Layer 4 - Grid slow counter-rotating
    py5.push_matrix()
    py5.rotate(-t * 0.15)
    draw_grid_lines(500, r, (50, 80, 80, 40))
    py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
