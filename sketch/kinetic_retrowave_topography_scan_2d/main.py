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

# Grid configuration
COLS = 60
ROWS = 40
SCL = 60 # Scale of each grid cell
W = COLS * SCL
H = ROWS * SCL

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 0, 20)
    py5.color_mode(py5.RGB, 255)

def draw():
    py5.background(10, 0, 20)
    
    flying = py5.frame_count * 0.05
    
    # Generate terrain height map
    terrain = np.zeros((COLS, ROWS))
    yoff = flying
    for y in range(ROWS):
        xoff = 0
        for x in range(COLS):
            # Mountains on the sides, valley in the center
            center_dist = abs(x - COLS/2) / (COLS/2)
            noise_val = py5.os_noise(xoff, yoff)
            
            # Combine noise with valley curve
            h_val = py5.remap(noise_val, 0, 1, -100, 300)
            h_val *= (center_dist ** 2) * 1.5 + 0.1
            
            terrain[x][y] = h_val
            xoff += 0.1
        yoff += 0.1

    # Camera / Projection setup for a fake 3D look in 2D
    py5.push_matrix()
    
    # Move to center bottom
    py5.translate(py5.width / 2, py5.height * 0.8)
    
    # We will do a manual pseudo-3D perspective projection.
    # We map (x, y, z) -> (px, py)
    # y is depth, x is left-right, z is height (terrain)
    
    focal_length = 800
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Draw horizontal lines
    for y in range(ROWS - 1):
        py5.begin_shape(py5.LINES)
        for x in range(COLS):
            # Point 1 (Current row)
            wx1 = (x - COLS/2) * SCL
            wy1 = y * SCL
            wz1 = terrain[x][y]
            
            # Map depth to perspective
            depth1 = wy1 + 400
            if depth1 <= 0: depth1 = 1
            scale1 = focal_length / depth1
            
            px1 = wx1 * scale1
            py1 = -wz1 * scale1 + (wy1 * 0.5) # Fake pitch down
            
            # Point 2 (Next row)
            wx2 = (x - COLS/2) * SCL
            wy2 = (y + 1) * SCL
            wz2 = terrain[x][y + 1]
            
            depth2 = wy2 + 400
            if depth2 <= 0: depth2 = 1
            scale2 = focal_length / depth2
            
            px2 = wx2 * scale2
            py2 = -wz2 * scale2 + (wy2 * 0.5)
            
            # Glitch/Laser logic
            scan_line = (py5.frame_count * 2) % ROWS
            if y == int(scan_line):
                py5.stroke(0, 255, 255, 255)
                py5.stroke_weight(4)
            else:
                # Distance fade and neon pink
                alpha = py5.remap(depth1, 400, H + 400, 255, 0)
                py5.stroke(255, 0, 150, alpha)
                py5.stroke_weight(2)
                
            py5.vertex(px1, py1)
            py5.vertex(px2, py2)
            
            # Horizontal connections (draw only for current row)
            if x < COLS - 1:
                wx3 = (x + 1 - COLS/2) * SCL
                wz3 = terrain[x + 1][y]
                px3 = wx3 * scale1
                py3 = -wz3 * scale1 + (wy1 * 0.5)
                
                py5.vertex(px1, py1)
                py5.vertex(px3, py3)
                
        py5.end_shape()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
