from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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

# Grid config
COLS = 160
ROWS = 90
CELL_W = SIZE[0] / COLS
CELL_H = SIZE[1] / ROWS

chars = np.array(list("0123456789ABCDEF@#$%&X+-"))
char_count = len(chars)

# Text tracking
current_chars = np.random.choice(chars, size=(ROWS, COLS))
char_ages = np.zeros((ROWS, COLS))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # We use a built-in font for simplicity, or just default text
    py5.text_font(py5.create_font("Courier New", 24))
    py5.text_align(py5.CENTER, py5.CENTER)
    
    py5.background(5, 5, 5)
    py5.color_mode(py5.RGB, 255)

def draw():
    global current_chars, char_ages
    
    # Trail / Fade
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.no_stroke()
    
    # Render loop
    # We iterate over a subset to keep performance high if needed, but numpy can help determine states.
    # Actually, let's build the noise field in numpy first.
    x_coords = np.linspace(0, 4, COLS)
    y_coords = np.linspace(0, 2.5, ROWS)
    
    for r in range(ROWS):
        for c in range(COLS):
            # Noise value for this cell
            n = py5.os_noise(x_coords[c], y_coords[r], t)
            
            # Flow magnitude
            flow = (n - 0.5) * 2.0
            
            # Age progression depends on flow
            char_ages[r, c] += abs(flow) * 0.1
            
            if char_ages[r, c] > 1.0:
                char_ages[r, c] = 0.0
                current_chars[r, c] = chars[py5.random_int(0, char_count - 1)]
            
            # Brightness based on flow intensity and age
            intensity = (1.0 - char_ages[r, c]) * abs(flow) * 255
            if intensity > 10:
                py5.fill(0, intensity, intensity * 0.3, intensity)
                py5.text(current_chars[r, c], c * CELL_W + CELL_W/2, r * CELL_H + CELL_H/2)
            
            # Highlights
            if intensity > 200:
                py5.fill(200, 255, 200, intensity)
                py5.text(current_chars[r, c], c * CELL_W + CELL_W/2, r * CELL_H + CELL_H/2)

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
