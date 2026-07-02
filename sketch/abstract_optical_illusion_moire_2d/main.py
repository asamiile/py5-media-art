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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.stroke_cap(py5.SQUARE)

def draw_layer(lines_count, radius, rotation, col, weight=2):
    py5.push_matrix()
    py5.rotate(rotation)
    py5.stroke(col)
    py5.stroke_weight(weight)
    angle_step = py5.TWO_PI / lines_count
    
    for i in range(lines_count):
        # Draw lines from a small inner radius to the outer radius
        py5.push_matrix()
        py5.rotate(i * angle_step)
        py5.line(50, 0, radius, 0)
        py5.pop_matrix()
    py5.pop_matrix()

def draw_concentric(rings_count, max_radius, center_offset, col, weight=2):
    py5.push_matrix()
    py5.translate(center_offset[0], center_offset[1])
    py5.no_fill()
    py5.stroke(col)
    py5.stroke_weight(weight)
    step = max_radius / rings_count
    for i in range(1, rings_count + 1):
        py5.circle(0, 0, i * step * 2)
    py5.pop_matrix()

def draw():
    py5.background(245, 245, 220) # Cream background
    
    time = py5.frame_count * 0.01
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    max_r = max(py5.width, py5.height)
    
    # Layer 1: Dense black concentric rings
    offset_x = py5.sin(time) * 100
    offset_y = py5.cos(time * 0.8) * 100
    draw_concentric(150, max_r, (offset_x, offset_y), py5.color(17, 17, 17), 3)
    
    # Layer 2: Dense black radial lines, counter-rotating
    draw_layer(360, max_r, -time * 0.5, py5.color(17, 17, 17), 4)
    
    # Layer 3: Crimson radial lines, co-rotating faster
    draw_layer(180, max_r, time * 1.2, py5.color(220, 20, 60), 3)
    
    # Layer 4: Royal Blue concentric rings, shifted center
    offset_x2 = py5.sin(time * 1.5 + py5.PI) * 150
    offset_y2 = py5.cos(time * 1.1 + py5.PI) * 150
    draw_concentric(100, max_r, (offset_x2, offset_y2), py5.color(65, 105, 225, 200), 4)

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
