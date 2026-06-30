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

MAX_DEPTH = 12

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(depth, length, t):
    if depth == 0:
        return
        
    # Thicker at base, thinner at tips
    thickness = (depth / MAX_DEPTH) * 15.0 + 1.0
    py5.stroke_weight(thickness)
    
    # Color: deeper teal at base, bright green at tips
    ratio = depth / MAX_DEPTH
    r = py5.remap(ratio, 1, 0, 17, 51)
    g = py5.remap(ratio, 1, 0, 136, 255)
    b = py5.remap(ratio, 1, 0, 136, 170)
    alpha = py5.remap(ratio, 1, 0, 100, 200)
    
    py5.stroke(r, g, b, alpha)
    py5.line(0, 0, 0, -length)
    
    py5.translate(0, -length)
    
    # Noise-driven angles
    noise_val1 = py5.os_noise(depth * 0.1, t * 0.5, 0)
    noise_val2 = py5.os_noise(depth * 0.1, t * 0.5, 100)
    
    base_angle = np.pi / 6  # 30 degrees
    angle1 = base_angle + noise_val1 * np.pi / 4
    angle2 = -base_angle + noise_val2 * np.pi / 4
    
    new_length = length * 0.75
    
    # Right branch
    py5.push_matrix()
    py5.rotate(angle1)
    draw_branch(depth - 1, new_length, t)
    py5.pop_matrix()
    
    # Left branch
    py5.push_matrix()
    py5.rotate(angle2)
    draw_branch(depth - 1, new_length, t)
    py5.pop_matrix()

def draw():
    # Subtractive trail effect
    py5.fill(5, 16, 21, 60)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / 60.0
    
    # Draw from bottom center
    py5.push_matrix()
    py5.translate(SIZE[0] / 2, SIZE[1])
    
    # Add some sway to the base
    sway = py5.os_noise(t * 0.2, 0) * 0.2
    py5.rotate(sway)
    
    draw_branch(MAX_DEPTH, SIZE[1] * 0.25, t)
    py5.pop_matrix()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.", flush=True)
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
