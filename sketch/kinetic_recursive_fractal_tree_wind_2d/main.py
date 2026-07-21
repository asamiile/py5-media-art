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

MAX_DEPTH = 14

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_branch(length, depth, branch_idx):
    if depth == 0:
        return
        
    py5.stroke_weight(max(1, depth * 0.8))
    
    # Calculate noise-driven wind angle
    # The higher up the tree (lower depth), the more it sways
    wind_factor = (MAX_DEPTH - depth) * 0.08
    
    t = py5.frame_count * 0.02
    # Add a global sway and localized leaf flutter
    noise_val = py5.noise(t + branch_idx * 0.1, depth * 0.2)
    angle_offset = (noise_val - 0.5) * wind_factor
    
    # Bioluminescent color mapping
    c_ratio = depth / MAX_DEPTH
    r = 20
    g = 150 + c_ratio * 105
    b_col = 100 + (1 - c_ratio) * 155
    py5.stroke(r, g, b_col, 150)
    
    # Draw current branch
    py5.line(0, 0, 0, -length)
    py5.translate(0, -length)
    
    # Two recursive branches
    py5.push_matrix()
    py5.rotate(0.5 + angle_offset)
    draw_branch(length * 0.77, depth - 1, branch_idx * 2)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate(-0.5 + angle_offset * 1.3)
    draw_branch(length * 0.77, depth - 1, branch_idx * 2 + 1)
    py5.pop_matrix()

def draw():
    # Very slight clear for glowing trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    # Draw three main trees
    tree_positions = [
        (SIZE[0] * 0.2, SIZE[1] * 0.9, SIZE[1] * 0.15),
        (SIZE[0] * 0.5, SIZE[1] * 0.95, SIZE[1] * 0.2),
        (SIZE[0] * 0.8, SIZE[1] * 0.9, SIZE[1] * 0.15)
    ]
    
    for idx, (tx, ty, tlen) in enumerate(tree_positions):
        py5.push_matrix()
        py5.translate(tx, ty)
        
        # slight global rotation per tree
        global_sway = (py5.noise(py5.frame_count * 0.01 + idx * 100) - 0.5) * 0.2
        py5.rotate(global_sway)
        
        draw_branch(tlen, MAX_DEPTH, idx)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
