from pathlib import Path
import shutil
import subprocess
import sys
import math
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

CELL_SIZE = 32
COLS = SIZE[0] // CELL_SIZE + 2
ROWS = SIZE[1] // CELL_SIZE + 2
CHARS = ["0", "1", "A", "B", "C", "D", "E", "F", "X", "Y", "Z", "<", ">", "=", "-", "+", "*", "#", "@", "%"]

grid_chars = []
for i in range(COLS):
    col = []
    for j in range(ROWS):
        col.append(random.choice(CHARS))
    grid_chars.append(col)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    font = py5.create_font("Courier New", CELL_SIZE * 0.8)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(2, 6, 2) 
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    for y in range(0, SIZE[1], 4):
        py5.stroke(0, 30, 0, 50)
        py5.stroke_weight(2)
        py5.line(0, y, SIZE[0], y)
        
    py5.no_stroke()
    
    for i in range(COLS):
        for j in range(ROWS):
            x = i * CELL_SIZE + CELL_SIZE / 2
            y = j * CELL_SIZE + CELL_SIZE / 2
            
            char = grid_chars[i][j]
            # Fast changing chars in noise clusters
            if py5.noise(i * 0.05, j * 0.05, t * 8) > 0.65:
                char = CHARS[(int(py5.noise(i, j, t * 30) * 100)) % len(CHARS)]
            
            glitch_noise = py5.noise(j * 0.02, t * 15)
            x_offset = 0
            
            # Horizontal sync tearing glitch
            if glitch_noise > 0.7:
                x_offset = py5.remap(glitch_noise, 0.7, 1.0, 0, CELL_SIZE * 15)
                x_offset *= math.sin(y * 0.05 + loop_t * 5)
                
            # Scanline bright bar moving down
            scanline_y = (t * SIZE[1] * 2) % SIZE[1]
            dist_to_scan = abs(y - scanline_y)
            # Make scanline wrap around
            if dist_to_scan > SIZE[1]/2:
                dist_to_scan = SIZE[1] - dist_to_scan
                
            brightness = 100
            if dist_to_scan < 150:
                brightness = py5.remap(dist_to_scan, 0, 150, 255, 100)
            
            x_pos = (x + x_offset) % SIZE[0]
            if x_pos < 0: x_pos += SIZE[0]
            
            py5.fill(30, brightness, 30, 220)
            py5.text(char, x_pos, y)
            
            if abs(x_offset) > 5 or brightness > 200:
                py5.fill(255, 0, 0, 180) 
                py5.text(char, (x_pos - max(x_offset * 0.1, 5)) % SIZE[0], y)
                py5.fill(0, 0, 255, 180) 
                py5.text(char, (x_pos + max(x_offset * 0.1, 5)) % SIZE[0], y)

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
