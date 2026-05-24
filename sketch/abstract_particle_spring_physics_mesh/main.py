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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Physics mesh parameters
COLS = 60
ROWS = 40
SPACING = 25.0

# Arrays for particles: [y, x] to map to grid easily
pos_x = np.zeros((ROWS, COLS))
pos_y = np.zeros((ROWS, COLS))
vel_x = np.zeros((ROWS, COLS))
vel_y = np.zeros((ROWS, COLS))
rest_x = np.zeros((ROWS, COLS))
rest_y = np.zeros((ROWS, COLS))

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize grid
    offset_x = (py5.width - (COLS - 1) * SPACING) / 2
    offset_y = (py5.height - (ROWS - 1) * SPACING) / 2
    
    for r in range(ROWS):
        for c in range(COLS):
            px = offset_x + c * SPACING
            py_c = offset_y + r * SPACING
            pos_x[r, c] = px
            pos_y[r, c] = py_c
            rest_x[r, c] = px
            rest_y[r, c] = py_c
            
def draw():
    global pos_x, pos_y, vel_x, vel_y
    
    py5.background(10)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    # Physics parameters
    spring_k = 0.05
    damping = 0.85
    
    # Invisible colliders that move through the mesh
    colliders = [
        {"x": py5.width/2 + py5.sin(t*0.5)*400, "y": py5.height/2 + py5.cos(t*0.7)*300, "r": 200},
        {"x": py5.width/2 + py5.cos(t*0.3)*500, "y": py5.height/2 + py5.sin(t*0.4)*200, "r": 150},
        {"x": py5.width/2 + py5.sin(t*0.9)*200, "y": py5.height/2 + py5.cos(t*1.1)*400, "r": 100}
    ]
    
    # Update physics
    # 1. Spring forces pulling particles back to rest position
    force_x = (rest_x - pos_x) * spring_k
    force_y = (rest_y - pos_y) * spring_k
    
    vel_x += force_x
    vel_y += force_y
    
    # 2. Add some turbulent noise
    for r in range(ROWS):
        for c in range(COLS):
            noise_val = py5.noise(r * 0.1, c * 0.1, t * 0.5)
            vel_x[r, c] += (noise_val - 0.5) * 1.5
            vel_y[r, c] += (noise_val - 0.5) * 1.5
    
    # 3. Collision forces
    for r in range(ROWS):
        for c in range(COLS):
            px = pos_x[r, c]
            py_c = pos_y[r, c]
            
            for col in colliders:
                dx = px - col["x"]
                dy = py_c - col["y"]
                dist_sq = dx*dx + dy*dy
                if dist_sq < col["r"]*col["r"]:
                    dist = np.sqrt(dist_sq)
                    if dist == 0: dist = 0.001
                    overlap = col["r"] - dist
                    # Push particle outwards
                    vel_x[r, c] += (dx / dist) * overlap * 0.2
                    vel_y[r, c] += (dy / dist) * overlap * 0.2
    
    # 4. Integrate and apply damping
    vel_x *= damping
    vel_y *= damping
    pos_x += vel_x
    pos_y += vel_y
    
    # Draw mesh lines
    py5.stroke_weight(1.0)
    
    # Horizontal lines
    for r in range(ROWS):
        for c in range(COLS - 1):
            x1, y1 = pos_x[r, c], pos_y[r, c]
            x2, y2 = pos_x[r, c+1], pos_y[r, c+1]
            
            # Distance stretch determines color
            dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            stretch = max(0, dist - SPACING)
            
            hue = (180 + stretch * 5 + t * 10) % 360
            brightness = min(100, 30 + stretch * 5)
            alpha = min(100, 20 + stretch * 2)
            
            py5.stroke(hue, 80, brightness, alpha)
            py5.line(x1, y1, x2, y2)
            
    # Vertical lines
    for c in range(COLS):
        for r in range(ROWS - 1):
            x1, y1 = pos_x[r, c], pos_y[r, c]
            x2, y2 = pos_x[r+1, c], pos_y[r+1, c]
            
            dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            stretch = max(0, dist - SPACING)
            
            hue = (280 + stretch * 5 + t * 10) % 360
            brightness = min(100, 30 + stretch * 5)
            alpha = min(100, 20 + stretch * 2)
            
            py5.stroke(hue, 80, brightness, alpha)
            py5.line(x1, y1, x2, y2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
