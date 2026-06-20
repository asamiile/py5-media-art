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

num_nodes = 300
nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize nodes in a spherical volume
    for _ in range(num_nodes):
        r = py5.random(100, 600)
        theta = py5.random(py5.TWO_PI)
        phi = py5.random(py5.PI)
        
        x = r * py5.sin(phi) * py5.cos(theta)
        y = r * py5.sin(phi) * py5.sin(theta)
        z = r * py5.cos(phi)
        
        nodes.append({
            "pos": np.array([x, y, z]),
            "base_pos": np.array([x, y, z]),
            "offset_speed": py5.random(0.01, 0.05),
            "hue": py5.random(160, 280), # cyan to purple
            "size": py5.random(2, 8)
        })

def draw():
    py5.background(5, 10, 15)
    
    py5.translate(py5.width/2, py5.height/2, -400)
    
    # Slowly rotate the entire constellation
    t = py5.frame_count
    py5.rotate_y(t * 0.005)
    py5.rotate_x(py5.sin(t * 0.002) * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    # Update positions with noise
    for i in range(num_nodes):
        node = nodes[i]
        bp = node["base_pos"]
        s = node["offset_speed"]
        
        nx = py5.os_noise(bp[0]*0.01, t*s) * 100 - 50
        ny = py5.os_noise(bp[1]*0.01, t*s + 100) * 100 - 50
        nz = py5.os_noise(bp[2]*0.01, t*s + 200) * 100 - 50
        
        node["pos"] = bp + np.array([nx, ny, nz])
        
    # Draw connections
    py5.stroke_weight(1)
    for i in range(num_nodes):
        p1 = nodes[i]["pos"]
        for j in range(i+1, num_nodes):
            p2 = nodes[j]["pos"]
            d = np.linalg.norm(p1 - p2)
            
            if d < 150:
                alpha = py5.remap(d, 0, 150, 80, 0)
                # Pulse based on time and distance
                pulse = (py5.sin(t * 0.1 - d * 0.05) + 1) * 0.5
                alpha *= pulse
                
                if alpha > 5:
                    avg_hue = (nodes[i]["hue"] + nodes[j]["hue"]) / 2
                    py5.stroke(avg_hue, 80, 100, alpha)
                    py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
                    
    # Draw nodes
    py5.no_stroke()
    for node in nodes:
        p = node["pos"]
        py5.push_matrix()
        py5.translate(p[0], p[1], p[2])
        py5.fill(node["hue"], 90, 100, 90)
        # Give some a glowing halo
        if node["size"] > 5:
            py5.fill(node["hue"], 90, 100, 30)
            py5.sphere(node["size"] * 2)
            py5.fill(node["hue"], 20, 100, 100)
            py5.sphere(node["size"] * 0.5)
        else:
            py5.box(node["size"])
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
