from pathlib import Path
import shutil
import subprocess
import sys
import random
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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.rect_mode(py5.CENTER)

def draw_fractal_cube(x, y, z, size, depth, max_depth, frame):
    py5.push_matrix()
    
    # Calculate glitch probability
    is_glitching = py5.os_noise(depth * 10, frame * 0.1) > 0.7
    
    if is_glitching:
        py5.translate(x + random.uniform(-10, 10), y + random.uniform(-10, 10), z + random.uniform(-10, 10))
    else:
        py5.translate(x, y, z)
        
    # Rotate based on depth and time
    rot_speed = py5.os_noise(depth * 5, frame * 0.005) * py5.TWO_PI
    py5.rotate_x(rot_speed)
    py5.rotate_y(rot_speed * 1.5)
    py5.rotate_z(rot_speed * 0.5)
    
    # Draw wireframe box
    hue_val = (180 + depth * 30 + frame * 0.5 + (180 if is_glitching else 0)) % 360
    py5.stroke(hue_val, 90, 100, 80)
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 4, 1))
    
    if is_glitching and random.random() > 0.5:
        py5.fill((hue_val + 180) % 360, 100, 100, 30)
    else:
        py5.no_fill()
        
    py5.box(size)
    
    if depth < max_depth:
        # Scale for children based on an oscillating sine wave
        child_scale = 0.5 + py5.sin(frame * 0.02 + depth) * 0.1
        child_size = size * child_scale
        offset = size / 2 + child_size / 2
        
        # Draw children in 6 directions
        draw_fractal_cube(offset, 0, 0, child_size, depth + 1, max_depth, frame)
        draw_fractal_cube(-offset, 0, 0, child_size, depth + 1, max_depth, frame)
        draw_fractal_cube(0, offset, 0, child_size, depth + 1, max_depth, frame)
        draw_fractal_cube(0, -offset, 0, child_size, depth + 1, max_depth, frame)
        draw_fractal_cube(0, 0, offset, child_size, depth + 1, max_depth, frame)
        draw_fractal_cube(0, 0, -offset, child_size, depth + 1, max_depth, frame)
        
    py5.pop_matrix()

def draw():
    # Glitch background clear
    if py5.frame_count % 120 == 0:
        py5.background(300, 80, 20)
    else:
        py5.background(0, 0, 5)
        
    py5.blend_mode(py5.ADD)
    
    # Camera orbital
    cam_radius = SIZE[1] * 1.5
    cam_x = py5.sin(py5.frame_count * 0.005) * cam_radius
    cam_z = py5.cos(py5.frame_count * 0.005) * cam_radius
    py5.camera(cam_x, py5.sin(py5.frame_count * 0.002) * SIZE[1], cam_z, 0, 0, 0, 0, 1, 0)
    
    draw_fractal_cube(0, 0, 0, SIZE[1] * 0.4, 0, 3, py5.frame_count)
    
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
