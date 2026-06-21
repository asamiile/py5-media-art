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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw_branch(length, depth, max_depth, time_val):
    if depth == 0:
        return
        
    py5.push_matrix()
    
    # Color based on depth
    hue = (120 + depth * 20 + time_val * 10) % 360
    py5.fill(hue, 80, 80)
    
    # Draw segment
    py5.box(length * 0.1, length, length * 0.1)
    
    # Move to the end of the segment
    py5.translate(0, length / 2, 0)
    
    # Calculate sway
    sway = py5.sin(time_val * 2.0 + depth * 0.5) * 0.1
    
    # Branching logic
    # Branch 1
    py5.push_matrix()
    py5.rotate_z(py5.PI / 6 + sway)
    py5.rotate_y(time_val) # Twist around Y
    py5.translate(0, length * 0.4, 0)
    draw_branch(length * 0.7, depth - 1, max_depth, time_val)
    py5.pop_matrix()
    
    # Branch 2
    py5.push_matrix()
    py5.rotate_z(-py5.PI / 6 + sway)
    py5.rotate_y(-time_val)
    py5.translate(0, length * 0.4, 0)
    draw_branch(length * 0.7, depth - 1, max_depth, time_val)
    py5.pop_matrix()
    
    # Branch 3 (3D effect, branch forward/backward)
    if depth > 2:
        py5.push_matrix()
        py5.rotate_x(py5.PI / 6 + sway)
        py5.translate(0, length * 0.4, 0)
        draw_branch(length * 0.7, depth - 1, max_depth, time_val)
        py5.pop_matrix()
        
        py5.push_matrix()
        py5.rotate_x(-py5.PI / 6 + sway)
        py5.translate(0, length * 0.4, 0)
        draw_branch(length * 0.7, depth - 1, max_depth, time_val)
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    py5.background(20, 20, 15)
    
    time_val = py5.frame_count * 0.02
    
    # Lighting
    py5.ambient_light(30, 30, 30)
    py5.directional_light(255, 0, 100, 1, 1, -1)
    py5.directional_light(200, 50, 100, -1, 1, 1)
    
    # Camera setup
    py5.translate(SIZE[0]/2, SIZE[1], -500)
    py5.rotate_x(-py5.PI / 8) # Tilt up slightly
    py5.rotate_y(py5.sin(time_val * 0.5) * 0.5) # Slow pan
    
    # Start tree facing upwards (processing Y is down, so we rotate 180 or use negative lengths)
    py5.rotate_z(py5.PI) 
    
    # Initial trunk
    draw_branch(400, 7, 7, time_val)

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
