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

cols = 0
rows = 0
grid = []
cell_size = 40

def setup():
    global cols, rows, grid
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.background(5, 16, 5)
    
    cols = py5.width // cell_size + 1
    rows = py5.height // cell_size + 1
    
    # Grid of objects: [active, y_pos, speed, hue_offset]
    for _ in range(cols):
        grid.append([False, 0.0, 0.0, 0])

def draw_glyph(x, y, size, seed):
    py5.push_matrix()
    py5.translate(x, y)
    py5.random_seed(seed)
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    for _ in range(3):
        rt = py5.random_int(3)
        if rt == 0:
            py5.rect(py5.random(size/2), py5.random(size/2), py5.random(size/2), py5.random(size/2))
        elif rt == 1:
            py5.line(py5.random(size), py5.random(size), py5.random(size), py5.random(size))
        else:
            py5.circle(py5.random(size), py5.random(size), py5.random(size))
            
    py5.pop_matrix()

def draw():
    global grid
    
    # Fade background
    py5.no_stroke()
    py5.fill(5, 16, 5, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    time = py5.frame_count
    
    # Update and draw grid columns
    for i in range(cols):
        # Randomly activate columns
        if not grid[i][0] and py5.random(1) < 0.02:
            grid[i] = [True, -cell_size, py5.random(5, 15), py5.random_int(100)]
            
        if grid[i][0]:
            x = i * cell_size
            y = grid[i][1]
            speed = grid[i][2]
            
            # Glow effect
            py5.stroke(0, 255, 65, 200)
            if py5.random(1) < 0.1:
                py5.stroke(0, 255, 255, 255) # Cyan glitch
                
            draw_glyph(x, y, cell_size * 0.8, abs(int(y)) + int(grid[i][3]))
            
            grid[i][1] += speed
            if grid[i][1] > py5.height + cell_size:
                grid[i][0] = False

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
