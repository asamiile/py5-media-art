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
DURATION_SEC = 10
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

def draw():
    py5.background(270, 80, 8) # Very dark synthwave purple
    py5.lights()
    
    # Position camera for a low-angle flyover effect
    py5.translate(SIZE[0] / 2, SIZE[1] / 2 + 300, -300)
    py5.rotate_x(py5.PI / 2.5) # Tilt camera to look down the horizon
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    cols = 90
    rows = 70
    scl = 40
    
    t_phase = (py5.frame_count / TOTAL_FRAMES) * py5.TWO_PI
    # Circular noise traversal ensures the terrain flowing loops perfectly
    cx = np.cos(t_phase) * 1.5
    cy = np.sin(t_phase) * 1.5
    
    # Draw the terrain using triangle strips
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            for y_offset in [0, 1]:
                curr_y = y + y_offset
                
                nx = x * 0.08
                ny = curr_y * 0.08
                
                # Z height mapped to noise
                z = py5.os_noise(nx, ny - cx, cy) * 600
                
                # Create a flat "highway" right down the center
                center_dist = abs(x - cols / 2.0)
                if center_dist < 8:
                    z *= (center_dist / 8.0) ** 2 # Smooth flatten
                
                # Color mapping based on height
                # Lower areas are purple (280), higher peaks are hot pink (330)
                hue = py5.remap(z, -300, 600, 280, 330)
                
                # Electric cyan grid lines
                py5.stroke(180, 100, 100, 40)
                py5.fill(hue, 90, 80, 90)
                
                px = x * scl - (cols * scl) / 2
                py_y = curr_y * scl - (rows * scl) / 2
                
                py5.vertex(px, py_y, z)
        py5.end_shape()

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
