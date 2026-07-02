from pathlib import Path
import shutil
import subprocess
import sys
import random
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

NUM_NODES = 400
CONNECTION_DIST = SIZE[1] * 0.25

class Node:
    def __init__(self):
        # Base position in a sphere
        r = SIZE[1] * 0.4 * math.cbrt(random.random())
        theta = random.uniform(0, py5.TWO_PI)
        phi = random.uniform(0, py5.PI)
        
        self.base_x = r * py5.sin(phi) * py5.cos(theta)
        self.base_y = r * py5.sin(phi) * py5.sin(theta)
        self.base_z = r * py5.cos(phi)
        
        self.x = self.base_x
        self.y = self.base_y
        self.z = self.base_z
        self.hue_offset = random.uniform(0, 360)
        
    def update(self, frame):
        # Jitter simulates quantum superposition
        noise_x = py5.os_noise(self.base_x * 0.01, self.base_y * 0.01, frame * 0.05) - 0.5
        noise_y = py5.os_noise(self.base_x * 0.01 + 100, self.base_y * 0.01, frame * 0.05) - 0.5
        noise_z = py5.os_noise(self.base_x * 0.01 + 200, self.base_y * 0.01, frame * 0.05) - 0.5
        
        # Orbital rotation
        rot_angle = frame * 0.005
        rx = self.base_x * py5.cos(rot_angle) - self.base_z * py5.sin(rot_angle)
        rz = self.base_x * py5.sin(rot_angle) + self.base_z * py5.cos(rot_angle)
        
        jitter_strength = 50 + py5.sin(frame * 0.02 + self.hue_offset) * 30
        
        self.x = rx + noise_x * jitter_strength
        self.y = self.base_y + noise_y * jitter_strength
        self.z = rz + noise_z * jitter_strength

nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_NODES):
        nodes.append(Node())

def draw():
    py5.background(10, 80, 5) # Very dark warm background
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Camera movement
    py5.rotate_x(py5.sin(py5.frame_count * 0.003) * py5.PI/6)
    py5.rotate_y(py5.cos(py5.frame_count * 0.004) * py5.PI/6)
    
    # Update nodes
    for node in nodes:
        node.update(py5.frame_count)
    
    # Draw connections (entanglement)
    py5.stroke_weight(2)
    py5.no_fill()
    
    for i in range(NUM_NODES):
        n1 = nodes[i]
        
        # Draw node
        hue = (n1.hue_offset + py5.frame_count * 0.5) % 360
        py5.push_matrix()
        py5.translate(n1.x, n1.y, n1.z)
        py5.no_stroke()
        py5.fill(hue, 80, 100, 80)
        py5.box(4)
        py5.pop_matrix()
        
        # Connect to neighbors
        for j in range(i + 1, NUM_NODES):
            n2 = nodes[j]
            dx = n1.x - n2.x
            dy = n1.y - n2.y
            dz = n1.z - n2.z
            dist_sq = dx*dx + dy*dy + dz*dz
            
            if dist_sq < CONNECTION_DIST * CONNECTION_DIST:
                dist = math.sqrt(dist_sq)
                alpha = py5.remap(dist, 0, CONNECTION_DIST, 80, 0)
                
                py5.stroke(hue, 60, 100, alpha)
                py5.line(n1.x, n1.y, n1.z, n2.x, n2.y, n2.z)

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
