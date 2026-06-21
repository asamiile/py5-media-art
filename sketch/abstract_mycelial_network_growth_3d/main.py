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
    py5.no_stroke()
    py5.sphere_detail(8)

def draw_branch(length, depth, max_depth, frame):
    if depth > max_depth:
        return
        
    # Animate growth
    current_length = min(length, length * (frame / (TOTAL_FRAMES * 0.5)) * (depth * 0.5 + 1))
    
    # Base color is dark purple/blue, tips are glowing cyan
    hue = py5.remap(depth, 0, max_depth, 260, 180)
    brightness = py5.remap(depth, 0, max_depth, 30, 100)
    py5.fill(hue, 80, brightness)
    
    # Draw cylinder segment
    py5.push_matrix()
    py5.translate(0, -current_length/2, 0)
    py5.box(length * 0.1 * (max_depth - depth + 1), current_length, length * 0.1 * (max_depth - depth + 1))
    py5.pop_matrix()
    
    py5.translate(0, -current_length, 0)
    
    # Only draw children if this branch has grown enough
    if current_length > length * 0.8:
        # Number of branches based on depth
        num_branches = 2 if depth > 2 else 3
        
        for i in range(num_branches):
            py5.push_matrix()
            
            # Organic rotation
            rot_y = py5.os_noise(depth * 10 + i, frame * 0.01) * py5.TWO_PI
            rot_z = py5.os_noise(depth * 20 + i, frame * 0.01 + 100) * py5.PI/3 + py5.PI/6
            
            py5.rotate_y(rot_y)
            py5.rotate_z(rot_z)
            
            # Branch gently sways
            sway = py5.sin(frame * 0.02 + depth + i) * 0.1
            py5.rotate_x(sway)
            
            draw_branch(length * 0.7, depth + 1, max_depth, frame)
            
            py5.pop_matrix()
            
        # Draw glowing spore at the tip
        if depth == max_depth:
            pulse = (py5.sin(frame * 0.1 + depth * 10) + 1) * 0.5
            py5.fill(180, 50, 100, 50 + pulse * 50)
            py5.sphere(length * 0.3 * (1 + pulse))

def draw():
    py5.background(240, 90, 5) # Very dark blue
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1] * 0.9, 0)
    
    # Camera rotates around the structure
    cam_radius = SIZE[1] * 1.2
    cam_x = py5.sin(py5.frame_count * 0.005) * cam_radius
    cam_z = py5.cos(py5.frame_count * 0.005) * cam_radius
    py5.camera(cam_x, py5.sin(py5.frame_count * 0.002) * SIZE[1] * 0.2 - SIZE[1]/2, cam_z, 0, -SIZE[1]/2, 0, 0, 1, 0)
    
    py5.ambient_light(260, 50, 20)
    py5.point_light(180, 80, 100, 0, -SIZE[1], 0)
    
    draw_branch(SIZE[1] * 0.25, 0, 6, py5.frame_count)
    
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
