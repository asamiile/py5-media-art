from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

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

# Cellular Automaton Properties
CELL_SIZE = 16
NUM_CELLS = 0
RULE = 90  # A cool fractal-like rule
history = []

def get_rule_bit(rule, left, center, right):
    # Rule index is defined by the binary value of the neighborhood
    index = (left << 2) | (center << 1) | right
    # Return the bit at that index in the rule number
    return (rule >> index) & 1

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global NUM_CELLS, history
    NUM_CELLS = py5.width // CELL_SIZE
    
    # Initialize with a random row
    first_row = np.random.randint(0, 2, NUM_CELLS, dtype=np.uint8)
    history.append(first_row)
    
    py5.background(0)

def draw():
    global history
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Very slowly fade background to black to create trails
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Calculate next generation
    prev = history[-1]
    next_gen = np.zeros(NUM_CELLS, dtype=np.uint8)
    
    # Dynamic rule switching based on time and noise
    # We switch between a few interesting chaotic rules (30, 90, 110, 150)
    rule_options = [30, 90, 110, 150]
    rule_idx = int((py5.noise(t * 5.0) * len(rule_options)) % len(rule_options))
    current_rule = rule_options[rule_idx]
    
    for i in range(NUM_CELLS):
        left = prev[i - 1] if i > 0 else prev[NUM_CELLS - 1]
        center = prev[i]
        right = prev[i + 1] if i < NUM_CELLS - 1 else prev[0]
        
        # Invert some bits randomly based on noise to mutate the CA and keep it from settling
        mutation = 1 if py5.noise(i * 0.1, t * 10.0) > 0.95 else 0
        
        next_gen[i] = get_rule_bit(current_rule, left, center, right) ^ mutation

    history.append(next_gen)
    
    # Keep history bounded by screen height
    max_history = (py5.height // CELL_SIZE) + 10
    if len(history) > max_history:
        history.pop(0)
        
    # Draw the history shifting downwards
    py5.no_stroke()
    
    y_offset = (py5.frame_count * 8) % CELL_SIZE
    
    for row_idx, row in enumerate(reversed(history)):
        y = row_idx * CELL_SIZE + y_offset
        
        if y > py5.height:
            continue
            
        # The higher up it is, the brighter it is
        alpha = py5.remap(y, 0, py5.height, 100, 0)
        
        for i, val in enumerate(row):
            if val == 1:
                x = i * CELL_SIZE
                # Matrix green to Cyan palette
                hue = (120 + t * 60 + py5.noise(i * 0.05) * 60) % 360
                py5.fill(hue, 100, 100, alpha)
                py5.rect(x, y, CELL_SIZE, CELL_SIZE)

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
