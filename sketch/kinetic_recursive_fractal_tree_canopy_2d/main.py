from pathlib import Path
import shutil
import subprocess
import sys
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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(length, depth, max_depth, x, y, tx, ty):
    if depth == 0:
        return
        
    py5.stroke_weight(depth * 1.5)
    
    progress = 1.0 - (depth / max_depth)
    hue = 180 + progress * 130
    py5.stroke(hue, 90, 40 + progress * 60, 60)
    
    py5.line(0, 0, 0, -length)
    py5.translate(0, -length)
    
    new_y = y - length
    
    n_val = py5.noise(x * 0.002, new_y * 0.002, tx)
    n_val2 = py5.noise(x * 0.002 + 100, new_y * 0.002 + 100, ty)
    
    angle1 = py5.PI / 6.5 
    angle2 = -py5.PI / 5.5 
    angle3 = py5.PI / 15 
    
    sway_amount = (progress * progress) * py5.PI / 4
    sway = (n_val - 0.5) * sway_amount + (n_val2 - 0.5) * sway_amount * 0.5
    
    if depth > 1:
        py5.push_matrix()
        py5.rotate(angle2 + sway)
        draw_branch(length * 0.75, depth - 1, max_depth, x - length * 0.5, new_y, tx, ty)
        py5.pop_matrix()
        
        py5.push_matrix()
        py5.rotate(angle1 + sway)
        draw_branch(length * 0.72, depth - 1, max_depth, x + length * 0.5, new_y, tx, ty)
        py5.pop_matrix()
        
        if depth % 2 == 0:
            py5.push_matrix()
            py5.rotate(angle3 + sway * 1.5)
            draw_branch(length * 0.6, depth - 1, max_depth, x, new_y, tx, ty)
            py5.pop_matrix()

def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.BLEND)
    py5.background(220, 80, 10) 
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    tx = math.cos(loop_t) * 0.8
    ty = math.sin(loop_t) * 0.8
    
    py5.push_matrix()
    py5.translate(SIZE[0] / 2, SIZE[1])
    draw_branch(400, 12, 12, SIZE[0] / 2, SIZE[1], tx, ty)
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
