from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    # Strictly black and white
    py5.color_mode(py5.RGB, 255)
    py5.background(255)

def draw_concentric_circles(cx, cy, max_radius, spacing):
    for r in range(spacing, max_radius, spacing):
        py5.ellipse(cx, cy, r * 2, r * 2)

def draw_radial_lines(cx, cy, length, num_lines):
    for i in range(num_lines):
        angle = (i / num_lines) * py5.TWO_PI
        x = cx + math.cos(angle) * length
        y = cy + math.sin(angle) * length
        py5.line(cx, cy, x, y)

def draw():
    py5.background(255)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.no_fill()
    py5.stroke(0)
    py5.stroke_weight(2)
    
    cx = py5.width / 2
    cy = py5.height / 2
    
    # Layer 1: Static background radial lines
    draw_radial_lines(cx, cy, py5.width, 360)
    
    # Layer 2: Slowly rotating foreground radial lines
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(t * py5.TWO_PI * 0.5)
    py5.translate(-cx, -cy)
    draw_radial_lines(cx, cy, py5.width, 360)
    py5.pop_matrix()
    
    # Layer 3: Concentric circles expanding from the center
    py5.stroke_weight(3)
    expansion = (t * 40) % 40
    # To animate the circles outwards seamlessly, we actually just shift their phase
    # A trick is to use an expanding ring loop
    for r in range(int(expansion), int(py5.width * 0.8), 40):
        if r > 10:
            py5.ellipse(cx, cy, r * 2, r * 2)
            
    # Layer 4: Oscillating horizontal and vertical grid lines for extreme moiré
    py5.stroke_weight(1.5)
    grid_spacing = 15
    offset_x = math.sin(t * py5.TWO_PI) * grid_spacing
    offset_y = math.cos(t * py5.TWO_PI * 2) * grid_spacing
    
    for x in range(0, py5.width, grid_spacing):
        py5.line(x + offset_x, 0, x + offset_x, py5.height)
        
    for y in range(0, py5.height, grid_spacing):
        py5.line(0, y + offset_y, py5.width, y + offset_y)
        
    # Layer 5: A slightly skewed overlay grid rotating counter-clockwise
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(-t * py5.TWO_PI * 0.1)
    py5.translate(-cx, -cy)
    for x in range(-py5.width, py5.width * 2, grid_spacing + 1):
        py5.line(x, -py5.height, x, py5.height * 2)
    for y in range(-py5.height, py5.height * 2, grid_spacing + 1):
        py5.line(-py5.width, y, py5.width * 2, y)
    py5.pop_matrix()

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
        import os
        os._exit(0)

py5.run_sketch()
