from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5
from scipy.spatial import Delaunay

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
cols = 60
rows = 40
scl = 60 # Scale of each grid cell
w = cols * scl
h = rows * scl

pts = []
triangles = []

def setup():
    global pts, triangles
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(20, 10, 40)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate points
    for y in range(rows):
        for x in range(cols):
            # Add some randomness to make it look organic
            nx = x * scl + random.uniform(-scl*0.4, scl*0.4)
            ny = y * scl + random.uniform(-scl*0.4, scl*0.4)
            pts.append([nx, ny])
            
    pts = np.array(pts)
    
    # Triangulate
    delaunay = Delaunay(pts)
    triangles = delaunay.simplices

def draw():
    py5.background(10, 5, 25) # Deep purple sky
    
    # Optional: Draw a sunset sun
    py5.no_stroke()
    py5.fill(255, 50, 100)
    py5.circle(SIZE[0]/2, SIZE[1]/2 - 200, 400)
    
    # We want to fly over the terrain, so we offset the noise in y-direction
    t = py5.frame_count * 0.01
    flying = t * 2.0
    
    # Calculate z for all points
    zs = np.zeros(len(pts))
    for i, (x, y) in enumerate(pts):
        noise_val = py5.os_noise(x * 0.005, y * 0.005 - flying)
        # We want high peaks and deep valleys
        zs[i] = py5.remap(noise_val, 0, 1, -200, 400)
        
    py5.push_matrix()
    # Center the terrain
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 200)
    
    # Simple perspective projection parameters
    # The terrain is flat on x, y and we view it from an angle
    # We'll map (x,y) -> (px, py)
    # Move origin to center of grid
    offset_x = w / 2
    offset_y = h / 2
    
    py5.stroke(0, 150)
    py5.stroke_weight(1)
    
    # To draw from back to front, we should sort triangles by average y
    # Actually, if we just draw them, they might overlap wrongly. 
    # Let's compute the center y for each triangle and sort.
    tri_data = []
    for tri in triangles:
        p0, p1, p2 = tri
        y_avg = (pts[p0][1] + pts[p1][1] + pts[p2][1]) / 3.0
        tri_data.append((y_avg, tri))
        
    tri_data.sort(key=lambda item: item[0]) # Draw back to front (low y first)
    
    for _, tri in tri_data:
        p0, p1, p2 = tri
        
        z0, z1, z2 = zs[p0], zs[p1], zs[p2]
        z_avg = (z0 + z1 + z2) / 3.0
        
        # Calculate color based on z_avg
        # Deep purple (20, 10, 80) to neon blue (0, 200, 255) to hot pink (255, 20, 147) to bright orange (255, 150, 0)
        if z_avg < 0:
            interp = py5.constrain(py5.remap(z_avg, -200, 0, 0, 1), 0, 1)
            r = py5.lerp(20, 0, interp)
            g = py5.lerp(10, 200, interp)
            b = py5.lerp(80, 255, interp)
        else:
            interp = py5.constrain(py5.remap(z_avg, 0, 400, 0, 1), 0, 1)
            r = py5.lerp(0, 255, interp)
            g = py5.lerp(200, 150, interp)
            b = py5.lerp(255, 0, interp)
            
        # Add lighting based on normal approximation (fake it using x gradient)
        # If the triangle points left or right, shade it differently
        dx = (pts[p1][0] - pts[p0][0])
        dz = z1 - z0
        shade = py5.constrain(py5.remap(dz/max(1, dx), -1, 1, 0.5, 1.5), 0.5, 1.5)
        
        py5.fill(r * shade, g * shade, b * shade)
        
        # Project
        # px = (x - offset_x)
        # py = (y - offset_y) * 0.4 - z
        
        def proj(idx):
            x, y = pts[idx]
            z = zs[idx]
            px = x - offset_x
            py_coord = (y - offset_y) * 0.35 - z
            return px, py_coord
            
        px0, py0 = proj(p0)
        px1, py1 = proj(p1)
        px2, py2 = proj(p2)
        
        py5.triangle(px0, py0, px1, py1, px2, py2)
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
