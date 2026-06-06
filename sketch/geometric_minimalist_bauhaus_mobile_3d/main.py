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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Primary colors
RED = (0, 90, 90)
BLUE = (220, 90, 90)
YELLOW = (50, 90, 100)
BLACK = (0, 0, 10)

def draw_mobile(depth, max_depth, t, seed):
    if depth > max_depth:
        return
        
    py5.random_seed(seed)
    
    # Arm length
    length = py5.random(150, 400) * (0.7 ** depth)
    angle = t * py5.random(0.5, 2.0) * (1 if py5.random(1) > 0.5 else -1)
    
    py5.push_matrix()
    py5.rotate_y(angle)
    
    # Draw horizontal arm
    py5.stroke(0, 0, 20)
    py5.stroke_weight(4 * (0.8 ** depth))
    py5.line(-length/2, 0, 0, length/2, 0, 0)
    
    # Left side
    py5.push_matrix()
    py5.translate(-length/2, 0, 0)
    # Draw string down
    drop_l = py5.random(50, 200) * (0.8 ** depth)
    py5.line(0, 0, 0, 0, drop_l, 0)
    py5.translate(0, drop_l, 0)
    
    if depth == max_depth or py5.random(1) > 0.6:
        # Draw shape
        py5.no_stroke()
        c = py5.random_choice([RED, BLUE, YELLOW, BLACK])
        py5.fill(*c)
        shape_type = py5.random_choice(["circle", "square", "triangle"])
        s = py5.random(40, 100) * (0.8 ** depth)
        
        # Billboard the shape so it faces the camera somewhat
        py5.rotate_y(-angle + t*0.2)
        if shape_type == "circle":
            py5.circle(0, 0, s)
        elif shape_type == "square":
            py5.rect_mode(py5.CENTER)
            py5.rect(0, 0, s, s)
        else:
            py5.triangle(-s/2, s/2, s/2, s/2, 0, -s/2)
    else:
        draw_mobile(depth + 1, max_depth, t, seed * 2)
    py5.pop_matrix()
    
    # Right side
    py5.push_matrix()
    py5.translate(length/2, 0, 0)
    # Draw string down
    drop_r = py5.random(50, 200) * (0.8 ** depth)
    py5.stroke(0, 0, 20)
    py5.line(0, 0, 0, 0, drop_r, 0)
    py5.translate(0, drop_r, 0)
    
    if depth == max_depth or py5.random(1) > 0.6:
        # Draw shape
        py5.no_stroke()
        c = py5.random_choice([RED, BLUE, YELLOW, BLACK])
        py5.fill(*c)
        shape_type = py5.random_choice(["circle", "square", "triangle"])
        s = py5.random(40, 100) * (0.8 ** depth)
        
        py5.rotate_y(-angle + t*0.3)
        if shape_type == "circle":
            py5.circle(0, 0, s)
        elif shape_type == "square":
            py5.rect_mode(py5.CENTER)
            py5.rect(0, 0, s, s)
        else:
            py5.triangle(-s/2, s/2, s/2, s/2, 0, -s/2)
    else:
        draw_mobile(depth + 1, max_depth, t, seed * 3 + 1)
    py5.pop_matrix()
    
    py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(40, 10, 95)  # Warm off-white background
    
    # Soft lighting
    py5.lights()
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 60, 0.5, 1, -0.5)
    
    py5.translate(py5.width / 2, 200, 0)
    
    # Main string from ceiling
    py5.stroke(0, 0, 20)
    py5.stroke_weight(5)
    py5.line(0, -400, 0, 0, 0, 0)
    
    t = py5.frame_count * 0.05
    py5.rotate_y(t * 0.1)
    
    # Draw mobile recursively
    draw_mobile(0, 4, t, 12345)

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2. Aborting.")
            import os
            os._exit(1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
