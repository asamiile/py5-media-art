from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Define a 3D cube vertices (x, y, z)
# Scaling from -1 to 1
vertices = np.array([
    [-1, -1, -1],
    [ 1, -1, -1],
    [ 1,  1, -1],
    [-1,  1, -1],
    [-1, -1,  1],
    [ 1, -1,  1],
    [ 1,  1,  1],
    [-1,  1,  1]
])

# Define the edges connecting the vertices
edges = [
    (0,1), (1,2), (2,3), (3,0), # back face
    (4,5), (5,6), (6,7), (7,4), # front face
    (0,4), (1,5), (2,6), (3,7)  # connecting edges
]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    # Enable a slight trail effect by not fully clearing the background
    py5.background(0)

def draw():
    # Fade background slightly for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 30) # Black with low opacity
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.blend_mode(py5.ADD)
    
    # Let's draw multiple rotating cubes!
    num_cubes = 5
    
    for i in range(num_cubes):
        
        # Calculate rotation angles based on time, offset per cube
        angle_x = t * py5.TWO_PI * 1.5 + (i * 0.2)
        angle_y = t * py5.TWO_PI * 2.0 + (i * 0.3)
        angle_z = t * py5.TWO_PI * 1.0 + (i * 0.1)
        
        # Rotation matrices
        rot_x = np.array([
            [1, 0, 0],
            [0, math.cos(angle_x), -math.sin(angle_x)],
            [0, math.sin(angle_x), math.cos(angle_x)]
        ])
        
        rot_y = np.array([
            [math.cos(angle_y), 0, math.sin(angle_y)],
            [0, 1, 0],
            [-math.sin(angle_y), 0, math.cos(angle_y)]
        ])
        
        rot_z = np.array([
            [math.cos(angle_z), -math.sin(angle_z), 0],
            [math.sin(angle_z), math.cos(angle_z), 0],
            [0, 0, 1]
        ])
        
        # Combine rotations (Z * Y * X)
        rot_matrix = rot_z @ rot_y @ rot_x
        
        # Scale of this cube
        cube_scale = 300 + i * 200 + math.sin(t * py5.TWO_PI + i) * 100
        
        # Apply rotation and projection to all vertices
        projected_points = []
        for v in vertices:
            # Rotate
            rotated = rot_matrix @ v
            
            # Distance for perspective
            distance = 4.0
            
            # Simple perspective projection
            z_div = 1.0 / (distance - rotated[2])
            
            # Projected X and Y
            # Fov factor
            fov = py5.height * 0.8
            proj_x = rotated[0] * z_div * fov
            proj_y = rotated[1] * z_div * fov
            
            # Add to list, scaling and centering
            px = py5.width / 2 + proj_x * (cube_scale / 300.0)
            py_final = py5.height / 2 + proj_y * (cube_scale / 300.0)
            projected_points.append((px, py_final, rotated[2]))
            
        # Draw edges
        # Color based on cube index
        hue1 = 160 # Neon Green
        hue2 = 320 # Electric Magenta
        hue = py5.lerp(hue1, hue2, i / float(num_cubes - 1))
        
        py5.stroke(hue, 90, 100)
        
        for edge in edges:
            p1 = projected_points[edge[0]]
            p2 = projected_points[edge[1]]
            
            # Thickness based on average Z depth (closer = thicker)
            avg_z = (p1[2] + p2[2]) / 2.0
            weight = py5.remap(avg_z, -2.0, 2.0, 1, 8)
            weight = max(0.5, float(weight))
            py5.stroke_weight(weight)
            
            py5.line(p1[0], p1[1], p2[0], p2[1])

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
        import os
        os._exit(0)

py5.run_sketch()
