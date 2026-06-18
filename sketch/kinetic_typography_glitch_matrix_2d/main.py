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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Allowed characters
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*<>"

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Try to load a monospace font if available, else use default
    font = py5.create_font("Courier New", 48)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.no_stroke()

def draw():
    # Motion blur / ghosting
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 10, 15, 60)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_t = py5.frame_count * 0.02
    
    cell_size = 60
    cols = py5.width // cell_size + 2
    rows = py5.height // cell_size + 2
    
    offset_x = (py5.width % cell_size) / 2 - cell_size
    offset_y = (py5.height % cell_size) / 2 - cell_size
    
    for i in range(cols):
        for j in range(rows):
            x = offset_x + i * cell_size + cell_size / 2
            y = offset_y + j * cell_size + cell_size / 2
            
            # Perlin noise for ripple and scale
            n_scale = py5.noise(i * 0.1, j * 0.1, time_t * 0.5)
            n_char = py5.noise(i * 0.2, j * 0.2, time_t * 0.2)
            
            # Glitch effect
            glitch_chance = py5.noise(j * 0.5, time_t * 2.0)
            is_glitch = glitch_chance > 0.85
            
            if is_glitch:
                x += random.uniform(-20, 20)
                n_scale *= random.uniform(1.2, 1.8)
                
            scale = py5.remap(n_scale, 0, 1, 0.1, 1.5)
            
            # Select character based on noise
            char_idx = int(py5.remap(n_char, 0, 1, 0, len(CHARS)))
            char_idx = py5.constrain(char_idx, 0, len(CHARS) - 1)
            char = CHARS[char_idx]
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.scale(scale)
            
            # Color logic
            base_alpha = int(py5.remap(n_scale, 0, 1, 50, 255))
            
            if is_glitch:
                # Chromatic aberration
                py5.fill(255, 50, 50, base_alpha) # Red channel
                py5.text(char, -4, 0)
                py5.fill(50, 50, 255, base_alpha) # Blue channel
                py5.text(char, 4, 0)
                py5.fill(255, 255, 255, base_alpha)
            else:
                # Matrix green-cyan
                r = int(py5.remap(n_scale, 0, 1, 0, 50))
                g = int(py5.remap(n_scale, 0, 1, 150, 255))
                b = int(py5.remap(n_char, 0, 1, 100, 255))
                py5.fill(r, g, b, base_alpha)
                
            py5.text(char, 0, 0)
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
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
