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

def setup():
    global l_system_str
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Simple L-System
    # Axiom: X
    # Rules: X -> F+[[X]-X]-F[-FX]+X, F -> FF
    
    axiom = "X"
    rules = {
        "X": "F+[[X]-X]-F[-FX]+X",
        "F": "FF"
    }
    
    # Generate the string (6 iterations max to avoid blowing up)
    l_system_str = axiom
    for _ in range(6):
        next_str = ""
        for char in l_system_str:
            next_str += rules.get(char, char)
        l_system_str = next_str
        
    py5.stroke_cap(py5.ROUND)

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def draw():
    py5.background(235, 225, 210) # Beige background
    py5.translate(py5.width / 2, py5.height - 100) # Start from bottom center
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Calculate global growth amount
    if t < 0.2:
        growth = ease_in_out(t / 0.2)
    elif t > 0.8:
        growth = ease_in_out((1.0 - t) / 0.2)
    else:
        growth = 1.0
        
    # Calculate global wind
    wind = py5.os_noise(t * 10.0, 0.0) - 0.5
    
    py5.stroke(40, 80, 50, 200) # Forest green
    py5.stroke_weight(6)
    
    # Draw L-System
    draw_len = 25 * growth
    base_angle = py5.radians(25)
    
    # Parse string
    drawn_elements = 0
    max_elements = int(len(l_system_str) * growth)
    
    cx = 0.0
    cy = 0.0
    current_angle = -py5.PI / 2 # pointing up
    stack = []
    
    for i, char in enumerate(l_system_str):
        if drawn_elements > max_elements:
            break
            
        # The angle includes wind which gets stronger higher up the tree (more drawn elements)
        angle_var = base_angle + wind * 0.2 * (drawn_elements / max(1, max_elements))
            
        if char == 'F':
            nx = cx + np.cos(current_angle) * draw_len
            ny = cy + np.sin(current_angle) * draw_len
            py5.line(cx, cy, nx, ny)
            cx = nx
            cy = ny
            drawn_elements += 1
        elif char == '+':
            current_angle += angle_var
        elif char == '-':
            current_angle -= angle_var
        elif char == '[':
            stack.append((cx, cy, current_angle))
        elif char == ']':
            if stack:
                cx, cy, current_angle = stack.pop()
            
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
