import math
from pathlib import Path
import shutil
import subprocess
import sys
import random
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

font = None

def setup():
    global font
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    font = py5.create_font("Monospaced", int(py5.width * 0.015))
    py5.text_font(font)
    py5.text_align(py5.LEFT, py5.TOP)
    random.seed(42)

def generate_hex_block(lines, chars_per_line):
    out = []
    for _ in range(lines):
        out.append("".join(random.choices("0123456789ABCDEF", k=chars_per_line)))
    return "\n".join(out)

def draw():
    py5.background(2, 5, 2) # Very dark phosphor green
    
    t = py5.frame_count / 60.0
    
    # 1. Draw crisp data to the canvas
    py5.fill(57, 255, 20) # Bright toxic phosphor green
    
    # Large data block on the left
    py5.text("SYSTEM DIAGNOSTICS: MEMORY DUMP", 100, 100)
    
    # Scroll offset
    scroll = int(t * 15)
    
    # We will generate deterministic random text based on frame count
    # so it scrolls up naturally.
    random.seed(int(scroll))
    for i in range(40):
        y = 150 + i * int(py5.width * 0.018)
        prefix = f"0x{(scroll + i) * 1024:08X} | "
        data = "".join(random.choices("0123456789ABCDEF <>-=+*", k=80))
        py5.text(prefix + data, 100, y)
        
    # Large graphic blocks on the right
    py5.text("STATUS: UNSTABLE", py5.width - 600, 100)
    for i in range(10):
        w = py5.width * random.uniform(0.05, 0.2)
        py5.rect(py5.width - 600, 150 + i * 50, w, 20)
        
    # Sine wave graph
    py5.no_fill()
    py5.stroke(57, 255, 20)
    py5.stroke_weight(3)
    py5.begin_shape()
    for x in range(py5.width - 600, py5.width - 100, 10):
        nx = x * 0.01 + t * 5.0
        y = 800 + math.sin(nx) * 100 * py5.os_noise(nx * 0.5, t)
        py5.vertex(x, y)
    py5.end_shape()
    
    # Overlay scanlines before grabbing pixels
    py5.stroke(0, 0, 0, 100)
    py5.stroke_weight(2)
    for y in range(0, py5.height, 6):
        py5.line(0, y, py5.width, y)
        
    # 2. Post-processing: Glitch and chromatic aberration
    py5.load_np_pixels()
    pixels = py5.np_pixels # Shape: (H, W, 4) in ARGB format
    
    # Glitch intensity driven by noise
    intensity = max(0, py5.os_noise(t * 2.0, 0.0) - 0.3) * 2.0
    if random.random() < 0.05:
        intensity += 2.0 # Sudden severe glitch
        
    if intensity > 0:
        h, w = pixels.shape[:2]
        new_pixels = np.copy(pixels)
        
        # Horizontal tracking tear (slice shift)
        num_tears = int(random.uniform(1, 5 * intensity))
        for _ in range(num_tears):
            tear_y = random.randint(0, h - 50)
            tear_h = random.randint(5, 50)
            tear_shift = int(random.uniform(-50, 50) * intensity)
            
            if tear_shift != 0:
                rolled = np.roll(new_pixels[tear_y:tear_y+tear_h, :, :], tear_shift, axis=1)
                new_pixels[tear_y:tear_y+tear_h, :, :] = rolled
                
        # Chromatic Aberration (RGB split)
        # ARGB format: A=0, R=1, G=2, B=3
        rgb_shift = int(10 * intensity)
        if rgb_shift > 0:
            # Shift Red right
            new_pixels[:, rgb_shift:, 1] = new_pixels[:, :-rgb_shift, 1]
            # Shift Blue left
            new_pixels[:, :-rgb_shift, 3] = new_pixels[:, rgb_shift:, 3]
            
        # Vertical Sync Roll
        if intensity > 1.5:
            roll_y = int((t * 800) % h)
            new_pixels = np.roll(new_pixels, roll_y, axis=0)
            
        py5.np_pixels[:] = new_pixels
        py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Basic safety check (run standard deviation on numpy array)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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
