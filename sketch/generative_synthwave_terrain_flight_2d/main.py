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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

COLS = 120
ROWS = 120
SCL = 80 # Distance between points in the 3D grid

W = COLS * SCL
H = ROWS * SCL

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global terrain_z_offset
    terrain_z_offset = 0.0

def draw():
    global terrain_z_offset
    
    # Solid background to clear frame
    py5.background(10, 5, 25)
    
    # Draw a retro glowing sun in the background
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2.5)
    py5.no_stroke()
    
    # Sun gradient
    for r in reversed(range(10, 800, 10)):
        progress = r / 800.0
        # Yellow to pink to purple
        py5.fill(255, 200 - 150 * progress, 50 + 200 * progress, 255 - 255 * progress)
        py5.circle(0, 0, r)
        
    py5.pop_matrix()
    
    # Generate the terrain heights using a fast double loop
    # We only need to generate it for the current frame
    terrain = np.zeros((ROWS, COLS))
    noise_scale = 0.08
    
    # Move the terrain forward over time
    flying_speed = 0.15
    terrain_z_offset -= flying_speed
    
    y_off = terrain_z_offset
    for y in range(ROWS):
        x_off = 0
        for x in range(COLS):
            # Noise returns 0 to 1
            # We map it to -150 to 500 for high mountains
            val = py5.noise(x_off, y_off)
            
            # Make the center flatter for a "valley" to fly through
            dist_from_center = abs(x - COLS/2) / (COLS/2)
            # Power curve to keep valley wide
            mountain_factor = dist_from_center ** 2.0 
            
            terrain[y, x] = (val * 800 - 100) * (0.2 + 0.8 * mountain_factor)
            
            x_off += noise_scale
        y_off += noise_scale

    # 3D Projection parameters
    fov = 600.0
    cam_y = 400.0 # Camera height above terrain
    cam_z = -300.0 # Camera Z position
    
    # Center the terrain in X
    start_x = -W / 2
    # Start the terrain at Z = 0
    start_z = 0
    
    py5.push_matrix()
    # Move to the center of the screen
    py5.translate(py5.width / 2, py5.height / 2 + 300)
    
    py5.stroke_weight(2)
    
    # Draw from back to front for proper painter's algorithm occlusion
    for y in reversed(range(ROWS - 1)):
        # Calculate world Z coordinates
        world_z1 = start_z + y * SCL
        world_z2 = start_z + (y + 1) * SCL
        
        # Calculate depth (distance from camera)
        depth1 = world_z1 - cam_z
        depth2 = world_z2 - cam_z
        
        # Prevent division by zero or negative depth
        if depth1 < 10 or depth2 < 10:
            continue
            
        py5.begin_shape(py5.QUAD_STRIP)
        for x in range(COLS):
            world_x = start_x + x * SCL
            
            height1 = terrain[y, x]
            height2 = terrain[y+1, x]
            
            # Color based on height
            # Map height (-100 to 700) to color
            h_norm1 = np.clip((height1 + 100) / 800, 0, 1)
            # Bright cyan/white peaks, deep magenta valleys
            r1 = 255 - 150 * (1 - h_norm1)
            g1 = 50 + 205 * h_norm1
            b1 = 255
            
            # Fill with solid black to occlude geometry behind it
            py5.fill(5, 0, 15)
            py5.stroke(r1, g1, b1)
            
            # Project point 1 (y)
            proj_x1 = (world_x / depth1) * fov
            proj_y1 = ((cam_y - height1) / depth1) * fov
            py5.vertex(proj_x1, proj_y1)
            
            # Project point 2 (y+1)
            h_norm2 = np.clip((height2 + 100) / 800, 0, 1)
            r2 = 255 - 150 * (1 - h_norm2)
            g2 = 50 + 205 * h_norm2
            b2 = 255
            
            py5.stroke(r2, g2, b2)
            proj_x2 = (world_x / depth2) * fov
            proj_y2 = ((cam_y - height2) / depth2) * fov
            py5.vertex(proj_x2, proj_y2)
            
        py5.end_shape()
        
    py5.pop_matrix()
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
