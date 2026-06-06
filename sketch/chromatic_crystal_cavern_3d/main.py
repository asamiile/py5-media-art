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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols, rows = 30, 40
scl = 150
w = cols * scl
h = rows * scl

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    # Use RGB to manually control chromatic aberration effects
    py5.color_mode(py5.RGB, 255, 255, 255, 255)

def draw_cavern(z_offset, channel_offset):
    terrain_top = np.zeros((cols, rows))
    terrain_bottom = np.zeros((cols, rows))
    
    flying = py5.frame_count * 0.05 + channel_offset * 0.5
    
    for x in range(cols):
        for y in range(rows):
            # Noise for cave roof and floor
            n_top = py5.os_noise(x * 0.15 + channel_offset, y * 0.15 + flying)
            n_bottom = py5.os_noise(x * 0.15 + 100 + channel_offset, y * 0.15 + flying)
            
            terrain_top[x][y] = py5.remap(n_top, -1, 1, -500, 100)
            terrain_bottom[x][y] = py5.remap(n_bottom, -1, 1, 100, 600)

    py5.push_matrix()
    py5.translate(-w / 2, -h / 2, z_offset)
    py5.rotate_x(py5.PI / 2)
    
    # Render cave
    py5.no_stroke()
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Set color based on channel to simulate chromatic split
            alpha = py5.remap(y, 0, rows, 255, 0) # Fade out in distance
            
            if channel_offset == 0:
                py5.fill(255, 0, 50, alpha) # Red tint
            elif channel_offset == 1:
                py5.fill(0, 255, 50, alpha) # Green tint
            else:
                py5.fill(50, 0, 255, alpha) # Blue tint
                
            # Floor
            py5.vertex(x * scl, y * scl, terrain_bottom[x][y])
            py5.vertex(x * scl, (y + 1) * scl, terrain_bottom[x][y + 1])
        py5.end_shape()
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Roof
            py5.vertex(x * scl, y * scl, terrain_top[x][y])
            py5.vertex(x * scl, (y + 1) * scl, terrain_top[x][y + 1])
        py5.end_shape()
        
    py5.pop_matrix()

def draw():
    py5.background(5, 5, 8)
    
    # We use additive blending for the chromatic dispersion
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    cam_rock = np.sin(py5.frame_count * 0.02) * 0.1
    py5.rotate_z(cam_rock)
    
    # Draw Red, Green, Blue layers with slight spatial and temporal offset
    draw_cavern(-800, 0)
    draw_cavern(-800, 1)
    draw_cavern(-800, 2)
    
    # Draw floating crystalline shards in the center
    py5.push_matrix()
    for i in range(20):
        py5.push_matrix()
        
        z_pos = (i * 200 + py5.frame_count * 30) % 4000 - 3000
        x_pos = np.sin(i * 123 + py5.frame_count * 0.01) * 600
        y_pos = np.cos(i * 321 + py5.frame_count * 0.01) * 300
        
        py5.translate(x_pos, y_pos, z_pos)
        py5.rotate_x(py5.frame_count * 0.02 + i)
        py5.rotate_y(py5.frame_count * 0.03 + i)
        
        py5.stroke(255, 255, 255, 100)
        py5.stroke_weight(2)
        py5.fill(100, 200, 255, 50)
        
        # Crystal shape
        py5.box(50, 150, 50)
        
        py5.pop_matrix()
    py5.pop_matrix()

    # Reset blend mode for next frame
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
