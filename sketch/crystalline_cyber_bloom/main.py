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
W, H = SIZE

def setup():
    # Use P3D renderer for hardware-accelerated 3D
    py5.size(W, H, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_recursive_box(size, depth, max_depth, t):
    if depth > max_depth:
        return
        
    py5.push_matrix()
    
    # Rotation depends on depth and time
    py5.rotate_x(t * 0.5 + depth * 0.2)
    py5.rotate_y(t * 0.3 - depth * 0.1)
    py5.rotate_z(t * 0.4 + depth * 0.15)
    
    # Pulse size
    pulse = 1.0 + 0.2 * np.sin(t * 2.0 + depth)
    s = size * pulse
    
    # Color based on depth and time
    hue = (200 + depth * 15 + t * 50) % 360
    sat = 80 - depth * 5
    bri = 90 + depth * 2
    alpha = 90 - depth * 5
    
    py5.fill(hue, sat, bri, alpha)
    
    # Draw wireframe-ish or solid box
    if depth % 2 == 0:
        py5.box(s)
    else:
        # Draw smaller accent boxes at corners
        offset = s / 2
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                for dz in [-1, 1]:
                    py5.push_matrix()
                    py5.translate(dx * offset, dy * offset, dz * offset)
                    py5.box(s * 0.3)
                    py5.pop_matrix()
    
    # Recurse
    new_size = size * 0.65
    
    # 6 directions
    offsets = [
        (new_size, 0, 0), (-new_size, 0, 0),
        (0, new_size, 0), (0, -new_size, 0),
        (0, 0, new_size), (0, 0, -new_size)
    ]
    
    for ox, oy, oz in offsets:
        py5.push_matrix()
        py5.translate(ox, oy, oz)
        draw_recursive_box(new_size, depth + 1, max_depth, t)
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    py5.background(15, 100, 10) # Dark navy background
    
    # Lighting
    py5.directional_light(0, 0, 100, 0, 1, -1)
    py5.directional_light(200, 50, 100, 1, 0, 0)
    py5.ambient_light(0, 0, 20)
    
    py5.translate(W / 2, H / 2, -500)
    
    # Smooth time variable
    t = py5.frame_count * (np.pi * 2 / TOTAL_FRAMES)
    
    # Slowly orbit camera
    py5.rotate_y(t)
    py5.rotate_x(np.sin(t) * 0.2)
    
    # Start recursion
    draw_recursive_box(H * 0.35, 0, 4, t)
    
    # Post-processing: not easily possible without filters, but py5 handles it
    
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
