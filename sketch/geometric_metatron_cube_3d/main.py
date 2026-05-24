from pathlib import Path
import shutil
import subprocess
import sys
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

# Metatron's Cube consists of 13 spheres.
# In 3D, we can represent this as a center sphere, and 12 spheres around it 
# matching the vertices of a cuboctahedron (or similar close-packing of spheres).
RADIUS = 250
nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate the 13 nodes
    nodes.append((0.0, 0.0, 0.0)) # Center
    
    # 12 outer nodes (vertices of an icosahedron or cuboctahedron)
    # Using cuboctahedron for classic tight packing (Vector Equilibrium)
    # Permutations of (±1, ±1, 0)
    outer = [
        (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
        (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
        (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1)
    ]
    
    for x, y, z in outer:
        # Normalize and scale
        mag = py5.sqrt(x*x + y*y + z*z)
        nodes.append((x/mag * RADIUS, y/mag * RADIUS, z/mag * RADIUS))
    
def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Complex 3D rotation
    py5.rotate_x(t)
    py5.rotate_y(t * 0.8)
    py5.rotate_z(t * 0.5)
    
    # Draw all connecting lines (Metatron's Cube logic: connect all centers)
    # There are 13 nodes, so 13 * 12 / 2 = 78 lines
    py5.no_fill()
    py5.stroke_weight(2)
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            x1, y1, z1 = nodes[i]
            x2, y2, z2 = nodes[j]
            
            # Distance from center for coloring
            dist1 = py5.sqrt(x1*x1 + y1*y1 + z1*z1)
            dist2 = py5.sqrt(x2*x2 + y2*y2 + z2*z2)
            
            # Pulse colors
            hue = (t * 50 + (dist1 + dist2) * 0.5) % 360
            
            # If it's a line connected to the center, make it brighter/thicker
            if i == 0:
                py5.stroke(hue, 100, 100, 90)
                py5.stroke_weight(3)
            else:
                py5.stroke(hue, 80, 80, 50)
                py5.stroke_weight(1)
                
            py5.line(x1, y1, z1, x2, y2, z2)
            
    # Draw the spheres
    py5.no_stroke()
    for i, (x, y, z) in enumerate(nodes):
        py5.push_matrix()
        py5.translate(x, y, z)
        
        hue = (t * 50 + i * 20) % 360
        py5.fill(hue, 90, 100, 90)
        
        # Rotating the inner sphere just for a lighting effect
        py5.rotate_y(t * 5)
        py5.sphere_detail(16)
        py5.sphere(25 if i == 0 else 15)
        py5.pop_matrix()

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
