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
from scipy.spatial import cKDTree

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_NODES = 400
CONNECTION_DISTANCE = 150
MAX_SPEED = 2.0

class NeuralOcean:
    def __init__(self):
        self.positions = np.random.rand(NUM_NODES, 3)
        self.positions[:, 0] *= SIZE[0]
        self.positions[:, 1] *= SIZE[1]
        self.positions[:, 2] *= 800
        self.positions[:, 2] -= 400
        
        self.velocities = (np.random.rand(NUM_NODES, 3) - 0.5) * 2
        
    def update(self, frame):
        # Apply 3D noise for currents
        time_offset = frame * 0.01
        currents = np.zeros_like(self.positions)
        for i in range(NUM_NODES):
            x, y, z = self.positions[i]
            # Custom simple pseudo-noise since we don't have direct py5 vector noise here easily
            nx = py5.os_noise(x * 0.002, y * 0.002, time_offset) - 0.5
            ny = py5.os_noise(x * 0.002, y * 0.002, time_offset + 100) - 0.5
            nz = py5.os_noise(x * 0.002, y * 0.002, time_offset + 200) - 0.5
            currents[i] = [nx, ny, nz]
            
        self.velocities += currents * 0.2
        
        # Limit speed
        speeds = np.linalg.norm(self.velocities, axis=1)
        too_fast = speeds > MAX_SPEED
        self.velocities[too_fast] = (self.velocities[too_fast].T / speeds[too_fast] * MAX_SPEED).T
        
        self.positions += self.velocities
        
        # Wrap around
        self.positions[:, 0] = np.mod(self.positions[:, 0], SIZE[0])
        self.positions[:, 1] = np.mod(self.positions[:, 1], SIZE[1])
        self.positions[:, 2] = np.where(self.positions[:, 2] > 400, -400, self.positions[:, 2])
        self.positions[:, 2] = np.where(self.positions[:, 2] < -400, 400, self.positions[:, 2])

ocean = NeuralOcean()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.sphere_detail(5)

def draw():
    py5.background(220, 90, 10)  # Deep navy blue
    
    # Enable additive blending
    py5.blend_mode(py5.ADD)
    
    ocean.update(py5.frame_count)
    
    tree = cKDTree(ocean.positions)
    pairs = tree.query_pairs(CONNECTION_DISTANCE)
    
    py5.stroke_weight(1.5)
    
    # Draw connections
    py5.begin_shape(py5.LINES)
    for i, j in pairs:
        p1 = ocean.positions[i]
        p2 = ocean.positions[j]
        
        # Calculate distance for opacity
        dist = np.linalg.norm(p1 - p2)
        alpha = py5.remap(dist, 0, CONNECTION_DISTANCE, 150, 0)
        
        # Color based on depth (z)
        z_avg = (p1[2] + p2[2]) / 2
        hue = py5.remap(z_avg, -400, 400, 180, 280)  # Cyan to Violet
        
        py5.stroke(hue, 80, 90, alpha)
        py5.vertex(p1[0], p1[1], p1[2])
        py5.vertex(p2[0], p2[1], p2[2])
    py5.end_shape()
    
    # Draw nodes
    py5.no_stroke()
    for i in range(NUM_NODES):
        x, y, z = ocean.positions[i]
        hue = py5.remap(z, -400, 400, 180, 280)
        py5.fill(hue, 80, 100, 200)
        py5.push_matrix()
        py5.translate(x, y, z)
        # Pulse size based on time and index
        pulse = py5.sin(py5.frame_count * 0.05 + i) * 2 + 3
        py5.sphere(pulse)
        py5.pop_matrix()

    # Fail-safe: abort if nothing is drawn

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
