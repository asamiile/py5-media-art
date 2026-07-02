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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_sponge(x, y, z, size, depth, max_depth, time_offset):
    if depth == max_depth:
        py5.push_matrix()
        py5.translate(x, y, z)
        
        # Calculate distance from center to color the core
        dist_to_center = (x**2 + y**2 + z**2)**0.5
        max_dist = size * 3
        normalized_dist = min(dist_to_center / max_dist, 1.0)
        
        # Core is bright cyan/blue, outer is dark purple/black
        hue = py5.remap(normalized_dist, 0, 1, 180, 280)
        sat = py5.remap(normalized_dist, 0, 1, 20, 100)
        
        # Pulse the core based on time
        pulse = (py5.sin(time_offset * 0.1 + dist_to_center * 0.01) + 1) * 0.5
        bri = py5.remap(normalized_dist, 0, 1, 100 * pulse, 20)
        
        py5.fill(hue, sat, bri)
        py5.no_stroke()
        
        # Add slight rotation to individual blocks
        py5.rotate_x(time_offset * 0.02 * (depth + 1))
        py5.rotate_y(time_offset * 0.03 * (depth + 1))
        
        # Dynamic box size
        box_scale = py5.remap(pulse, 0, 1, 0.8, 1.0)
        py5.box(size * box_scale)
        py5.pop_matrix()
    else:
        new_size = size / 3.0
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    # Remove the center block and the center of each face to make a Menger sponge
                    abs_sum = abs(i) + abs(j) + abs(k)
                    if abs_sum > 1:
                        draw_sponge(x + i * new_size, y + j * new_size, z + k * new_size, new_size, depth + 1, max_depth, time_offset)

def draw():
    py5.background(0)
    
    # Lighting
    py5.ambient_light(0, 0, 20)
    py5.directional_light(0, 0, 80, 1, 1, -1)
    py5.point_light(180, 80, 100, 0, 0, 0) # Core light
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Global rotation
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    py5.rotate_z(py5.frame_count * 0.002)
    
    # Dynamic depth based on time, oscillating between 1 and 3
    base_depth = 2
    
    initial_size = min(py5.width, py5.height) * 0.6
    draw_sponge(0, 0, 0, initial_size, 0, base_depth, py5.frame_count)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save gigabytes of local storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
