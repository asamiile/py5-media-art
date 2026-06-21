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

def draw_fractal(x, y, r, depth, max_depth, time_val):
    if depth > max_depth:
        return
        
    # Color based on depth and time
    hue = (depth * 40 + time_val * 100) % 360
    py5.stroke(hue, 80, 100, 150)
    py5.fill(hue, 60, 100, 50)
    
    py5.push_matrix()
    py5.translate(x, y)
    
    # Rotate each layer slightly differently
    rot_angle = py5.sin(time_val * 0.5 + depth * 0.2) * py5.TWO_PI
    py5.rotate(rot_angle)
    
    # Draw geometric shape
    sides = 3 + (depth % 4) # Vary shape by depth
    py5.begin_shape()
    for i in range(sides):
        angle = py5.TWO_PI * i / sides
        px = py5.cos(angle) * r
        py = py5.sin(angle) * r
        py5.vertex(px, py)
    py5.end_shape(py5.CLOSE)
    
    # Branch out
    branches = 4
    for i in range(branches):
        branch_angle = (py5.TWO_PI * i / branches) + time_val * 0.2
        bx = py5.cos(branch_angle) * r * 0.8
        by = py5.sin(branch_angle) * r * 0.8
        
        # Scale down
        new_r = r * 0.5 * (1 + py5.sin(time_val + depth) * 0.2)
        draw_fractal(bx, by, new_r, depth + 1, max_depth, time_val)
        
    py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur / trails
    py5.no_stroke()
    py5.fill(0, 0, 10, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.02
    
    # Draw the main fractal at the center
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    # Slow rotation of the entire piece
    py5.rotate(time_val * 0.1)
    py5.stroke_weight(2)
    draw_fractal(0, 0, SIZE[1] * 0.3, 0, 5, time_val)
    py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
