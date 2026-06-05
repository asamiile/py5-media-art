from pathlib import Path
import shutil
import subprocess
import sys
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

def draw_fractal(level, size):
    if level == 0:
        py5.box(size)
    else:
        new_size = size / 3.0
        offset = new_size
        
        # Draw 8 corner boxes to form a recursive hollow structure
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    # Keep corners and edges, remove faces and center
                    abs_sum = abs(dx) + abs(dy) + abs(dz)
                    if abs_sum >= 2:
                        py5.push_matrix()
                        py5.translate(dx * offset, dy * offset, dz * offset)
                        draw_fractal(level - 1, new_size)
                        py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
def draw():
    py5.background(0) # Pitch black for additive blending
    
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.02
    
    base_rot_x = py5.frame_count * 0.005
    base_rot_y = py5.frame_count * 0.007
    base_rot_z = py5.frame_count * 0.003
    
    # Simulate chromatic aberration by rendering the same fractal 3 times
    # with slightly different rotations and colors
    
    channels = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255)     # Blue
    ]
    
    # Pulse scale
    scale_factor = 1.0 + np.sin(t) * 0.1
    
    for i, color in enumerate(channels):
        py5.push_matrix()
        
        # Chromatic offset
        offset_angle = i * 0.01 * np.sin(t * 0.5)
        
        py5.rotate_x(base_rot_x + offset_angle)
        py5.rotate_y(base_rot_y - offset_angle)
        py5.rotate_z(base_rot_z + offset_angle * 0.5)
        
        # Pulsing scale with slight channel offset
        py5.scale(scale_factor + i * 0.005)
        
        py5.fill(*color, 150)
        
        # Draw a level 3 Menger-like fractal
        draw_fractal(3, 800)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
