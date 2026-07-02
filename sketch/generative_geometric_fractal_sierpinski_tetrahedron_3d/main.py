from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math

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

MAX_DEPTH = 5

# Define the 4 vertices of a regular tetrahedron
# Coordinates for a regular tetrahedron inscribed in a unit sphere
verts = [
    (math.sqrt(8/9), 0, -1/3),
    (-math.sqrt(2/9), math.sqrt(2/3), -1/3),
    (-math.sqrt(2/9), -math.sqrt(2/3), -1/3),
    (0, 0, 1)
]

def draw_tetrahedron():
    py5.begin_shape(py5.TRIANGLES)
    # Face 1 (0, 1, 2)
    py5.vertex(*verts[0])
    py5.vertex(*verts[1])
    py5.vertex(*verts[2])
    # Face 2 (0, 1, 3)
    py5.vertex(*verts[0])
    py5.vertex(*verts[1])
    py5.vertex(*verts[3])
    # Face 3 (1, 2, 3)
    py5.vertex(*verts[1])
    py5.vertex(*verts[2])
    py5.vertex(*verts[3])
    # Face 4 (2, 0, 3)
    py5.vertex(*verts[2])
    py5.vertex(*verts[0])
    py5.vertex(*verts[3])
    py5.end_shape()

def draw_sierpinski(depth, scale, breath_factor, hue_base):
    if depth == 0:
        py5.fill(hue_base, 80, 100)
        py5.push_matrix()
        py5.scale(scale)
        draw_tetrahedron()
        py5.pop_matrix()
    else:
        new_scale = scale * 0.5
        # The offset is distance from origin to new center.
        # For a standard Sierpinski, the new centers are halfway to the vertices.
        # We multiply by breath_factor to make it expand/contract.
        offset_dist = scale * 0.5 * breath_factor
        
        for i in range(4):
            py5.push_matrix()
            dx = verts[i][0] * offset_dist
            dy = verts[i][1] * offset_dist
            dz = verts[i][2] * offset_dist
            py5.translate(dx, dy, dz)
            
            new_hue = (hue_base + 30) % 360
            draw_sierpinski(depth - 1, new_scale, breath_factor, new_hue)
            py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 10, 20)
    
    t = py5.frame_count * 0.02
    
    # Lighting
    py5.ambient_light(0, 0, 30)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(200, 50, 80, -1, 0.5, -1)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.PI / 4 + py5.sin(t * 0.3) * 0.2)
    py5.rotate_z(t * 0.2)
    
    # Breathing animation: 1.0 is touching, > 1.0 is exploded
    breath = 1.0 + max(0, py5.sin(t * 2)) * 0.5
    
    py5.no_stroke()
    
    initial_scale = 800
    base_hue = (t * 20) % 360
    
    draw_sierpinski(MAX_DEPTH, initial_scale, breath, base_hue)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
