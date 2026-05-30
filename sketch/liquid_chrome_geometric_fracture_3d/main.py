from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

# Generate a rough sphere of triangles
faces = []
RADIUS = 250

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global faces
    
    # Simple icosphere-like generation or latitude/longitude sphere
    lats = 30
    lons = 30
    
    vertices = []
    for i in range(lats + 1):
        lat_angle = py5.remap(i, 0, lats, 0, py5.PI)
        for j in range(lons + 1):
            lon_angle = py5.remap(j, 0, lons, 0, py5.TWO_PI)
            
            x = RADIUS * np.sin(lat_angle) * np.cos(lon_angle)
            y = RADIUS * np.sin(lat_angle) * np.sin(lon_angle)
            z = RADIUS * np.cos(lat_angle)
            vertices.append(np.array([x, y, z]))
            
    # Connect vertices into triangles
    for i in range(lats):
        for j in range(lons):
            v1 = i * (lons + 1) + j
            v2 = v1 + 1
            v3 = (i + 1) * (lons + 1) + j
            v4 = v3 + 1
            
            # Add two triangles per quad
            # We also compute the normal of the triangle to push it out later
            p1 = vertices[v1]
            p2 = vertices[v2]
            p3 = vertices[v3]
            
            # Triangle 1
            n1 = np.cross(p2 - p1, p3 - p1)
            n_len = np.linalg.norm(n1)
            if n_len > 0: n1 /= n_len
            center1 = (p1 + p2 + p3) / 3.0
            
            faces.append({
                "v": [p1, p2, p3],
                "normal": n1,
                "center": center1,
                "rot_speed": np.random.randn(3) * 0.05
            })
            
            # Triangle 2
            p4 = vertices[v4]
            n2 = np.cross(p3 - p2, p4 - p2)
            n_len = np.linalg.norm(n2)
            if n_len > 0: n2 /= n_len
            center2 = (p2 + p4 + p3) / 3.0
            
            faces.append({
                "v": [p2, p4, p3],
                "normal": n2,
                "center": center2,
                "rot_speed": np.random.randn(3) * 0.05
            })


def draw():
    py5.background(20) # Deep void grey
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.02
    
    # Chrome lighting setup
    py5.light_specular(255, 255, 255) # White specular highlights
    py5.directional_light(30, 100, 80, -1, 1, -1) # Warm orange
    py5.directional_light(200, 100, 100, 1, -1, -0.5) # Cold blue
    py5.ambient_light(50, 50, 50)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Global rotation
    py5.rotate_y(t * 0.3)
    py5.rotate_x(t * 0.2)
    
    # Material properties
    py5.specular(255, 255, 255)
    py5.shininess(50)
    
    py5.fill(0, 0, 90) # Base silver/grey
    py5.no_stroke()
    
    # Fracture wave
    fracture_amount = (np.sin(t) * 0.5 + 0.5) # 0 to 1
    # Add a little noise so it's not totally uniform
    
    for f in faces:
        py5.push_matrix()
        
        # Calculate how far to push this face out based on its center
        n = py5.os_noise(f["center"][0]*0.01, f["center"][1]*0.01, t)
        
        # Explosion offset
        offset = f["normal"] * (fracture_amount * n * 800)
        
        py5.translate(*offset)
        
        # If fractured, also spin the shards
        if fracture_amount > 0.05:
            # We translate to center, rotate, translate back to spin in place
            py5.translate(*f["center"])
            py5.rotate_x(t * f["rot_speed"][0] * fracture_amount * 20)
            py5.rotate_y(t * f["rot_speed"][1] * fracture_amount * 20)
            py5.rotate_z(t * f["rot_speed"][2] * fracture_amount * 20)
            py5.translate(*(-f["center"]))
            
        py5.begin_shape(py5.TRIANGLES)
        # py5.normal(*f["normal"])
        py5.vertex(*f["v"][0])
        py5.vertex(*f["v"][1])
        py5.vertex(*f["v"][2])
        py5.end_shape()
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            
        os._exit(0)

py5.run_sketch()
