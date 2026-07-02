from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_crystals = 300
crystals = np.zeros((num_crystals, 7), dtype=np.float32) # x, y, z, size, rot_x, rot_y, rot_z

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    tunnel_radius = 600
    tunnel_length = 8000
    
    for i in range(num_crystals):
        # Position crystals along the walls of a cylindrical tunnel
        angle = py5.random(py5.TWO_PI)
        r = py5.random(tunnel_radius * 0.8, tunnel_radius * 1.5)
        
        crystals[i, 0] = py5.cos(angle) * r
        crystals[i, 1] = py5.sin(angle) * r
        crystals[i, 2] = py5.random(-tunnel_length, tunnel_length)
        
        crystals[i, 3] = py5.random(100, 400) # Size
        
        crystals[i, 4] = py5.random(py5.TWO_PI) # Rot x
        crystals[i, 5] = py5.random(py5.TWO_PI) # Rot y
        crystals[i, 6] = py5.random(py5.TWO_PI) # Rot z

def draw_crystal(size):
    # A simple geometric crystal (octahedron-like)
    py5.begin_shape(py5.TRIANGLES)
    
    # Top point
    p_top = (0, -size, 0)
    # Bottom point
    p_bot = (0, size, 0)
    
    # Mid points
    pm1 = (-size*0.5, 0, -size*0.5)
    pm2 = (size*0.5, 0, -size*0.5)
    pm3 = (size*0.5, 0, size*0.5)
    pm4 = (-size*0.5, 0, size*0.5)
    
    # Top pyramid
    py5.vertex(*p_top); py5.vertex(*pm1); py5.vertex(*pm2)
    py5.vertex(*p_top); py5.vertex(*pm2); py5.vertex(*pm3)
    py5.vertex(*p_top); py5.vertex(*pm3); py5.vertex(*pm4)
    py5.vertex(*p_top); py5.vertex(*pm4); py5.vertex(*pm1)
    
    # Bottom pyramid
    py5.vertex(*p_bot); py5.vertex(*pm1); py5.vertex(*pm2)
    py5.vertex(*p_bot); py5.vertex(*pm2); py5.vertex(*pm3)
    py5.vertex(*p_bot); py5.vertex(*pm3); py5.vertex(*pm4)
    py5.vertex(*p_bot); py5.vertex(*pm4); py5.vertex(*pm1)
    
    py5.end_shape()

def draw():
    py5.background(10, 50, 10) # Dark deep green/blue
    
    time = py5.frame_count * 0.01
    
    # Camera movement: fly through the tunnel
    cam_z = (py5.frame_count * 25) % 8000 - 4000
    cam_x = py5.sin(time) * 200
    cam_y = py5.cos(time * 0.8) * 200
    
    py5.camera(cam_x, cam_y, cam_z,
               cam_x * 0.5, cam_y * 0.5, cam_z - 1000,
               0, 1, 0)
               
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    # Point lights for reflections
    py5.point_light(300, 80, 100, cam_x, cam_y, cam_z)
    py5.point_light(180, 80, 100, cam_x, cam_y, cam_z - 2000)
    
    for i in range(num_crystals):
        z_dist = crystals[i, 2] - cam_z
        
        # Wrapping crystals so the tunnel goes on forever
        while z_dist > 2000:
            crystals[i, 2] -= 8000
            z_dist = crystals[i, 2] - cam_z
        while z_dist < -6000:
            crystals[i, 2] += 8000
            z_dist = crystals[i, 2] - cam_z
            
        # Only draw if roughly in front of camera
        if z_dist < 500 and z_dist > -5000:
            py5.push_matrix()
            py5.translate(crystals[i, 0], crystals[i, 1], crystals[i, 2])
            
            # Slow rotation
            py5.rotate_x(crystals[i, 4] + time * 0.2)
            py5.rotate_y(crystals[i, 5] + time * 0.3)
            py5.rotate_z(crystals[i, 6] + time * 0.1)
            
            # Base color depending on angle
            hue = (i * 15 + time * 50) % 360
            
            py5.fill(hue, 80, 50, 60) # Semi-transparent
            
            draw_crystal(crystals[i, 3])
            
            # Add a white wireframe for glowing edges
            py5.stroke(hue, 20, 100, 80)
            py5.stroke_weight(2)
            py5.no_fill()
            draw_crystal(crystals[i, 3] * 1.05)
            py5.no_stroke()
            
            py5.pop_matrix()
            
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
