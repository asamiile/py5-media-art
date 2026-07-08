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

GRID_COLS = 35
GRID_ROWS = 35
SPACING = 60
CHARSET = [chr(i) for i in range(0x30A0, 0x30FF)] + [str(i) for i in range(10)]

def get_char():
    return random.choice(CHARSET)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text_size(20)
    
def draw():
    py5.background(10, 20, 15)
    
    t = py5.frame_count * 0.02
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    angle = py5.PI / 4 + t * 0.05
    py5.scale(1.0, 0.5)
    py5.rotate(angle)
    
    offset_x = (GRID_COLS - 1) * SPACING / 2
    offset_y = (GRID_ROWS - 1) * SPACING / 2
    
    # Simple depth sorting hack: draw based on distance along the viewing axis
    # View vector is (cos(angle + pi/2), sin(angle + pi/2))
    view_x = math.cos(angle + py5.PI / 2)
    view_y = math.sin(angle + py5.PI / 2)
    
    points = []
    for i in range(GRID_COLS):
        for j in range(GRID_ROWS):
            x = i * SPACING - offset_x
            y = j * SPACING - offset_y
            depth = x * view_x + y * view_y
            points.append((x, y, i, j, depth))
            
    # Sort by depth descending so furthest points draw first
    points.sort(key=lambda p: p[4], reverse=True)
    
    for pt in points:
        x, y, i, j, depth = pt
        
        noise_val = py5.noise(i * 0.15, j * 0.15, t * 0.4)
        pillar_height = int(py5.remap(noise_val, 0, 1, 1, 20))
        
        dist = math.sqrt(x*x + y*y)
        wave = (math.sin(dist * 0.008 - t * 3) + 1) / 2
        pillar_height += int(wave * 15)
        
        hue = (140 + dist * 0.05 + t * 30) % 360
        
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(-angle)
        py5.scale(1.0, 2.0)
        
        for h_idx in range(pillar_height):
            draw_y = -h_idx * 16
            
            brightness = py5.remap(h_idx, 0, pillar_height, 10, 100)
            alpha = py5.remap(h_idx, 0, pillar_height, 20, 100)
            
            if h_idx == pillar_height - 1:
                py5.fill(0, 0, 100, 100) 
            else:
                py5.fill(hue, 90, brightness, alpha)
                
            char = get_char() if random.random() > 0.1 else " " 
            
            if char != " ":
                py5.text(char, 0, draw_y)
                
        py5.pop_matrix()

    py5.color_mode(py5.RGB, 255)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
