from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Fragment:
    def __init__(self, pos, vertices):
        self.pos = np.array(pos)
        self.orig_pos = np.copy(self.pos)
        self.vertices = vertices # Relative to pos
        self.vel = np.array([0.0, 0.0])
        
        # Determine initial color based on distance to center
        dist_to_center = np.linalg.norm(self.pos - np.array([SIZE[0]/2, SIZE[1]/2]))
        self.health = 1.0 # 1.0 = alive, 0.0 = apoptotic body
        
        # We will stagger the "death" of each cell based on noise
        self.death_time = py5.random(0.2, 0.8) + py5.os_noise(self.pos[0]*0.01, self.pos[1]*0.01) * 0.2
        
        # Rotational drift once dead
        self.rot = 0.0
        self.rot_vel = py5.random(-0.05, 0.05)
        
    def update(self, t):
        # Progress of apoptosis for this specific cell
        progress = py5.remap(t, max(0, self.death_time - 0.2), min(1.0, self.death_time + 0.2), 1.0, 0.0)
        self.health = max(0.0, min(1.0, progress))
        
        if self.health < 1.0:
            # Begin to drift away from center
            push_dir = self.pos - np.array([SIZE[0]/2, SIZE[1]/2])
            push_dir = push_dir / (np.linalg.norm(push_dir) + 0.001)
            
            # Add some noise to the drift
            nx = py5.os_noise(self.pos[0]*0.01, t*2) * 2 - 1
            ny = py5.os_noise(self.pos[1]*0.01, t*2+100) * 2 - 1
            
            self.vel += (push_dir * 0.5 + np.array([nx, ny])) * (1.0 - self.health) * 0.1
            self.pos += self.vel
            
            self.rot += self.rot_vel * (1.0 - self.health)

    def draw(self, t):
        py5.push_matrix()
        py5.translate(self.pos[0], self.pos[1])
        
        # Apply shrinking and rotation as it dies
        scale = py5.remap(self.health, 1.0, 0.0, 1.0, 0.3)
        py5.scale(scale)
        py5.rotate(self.rot)
        
        # Color shifts from warm (alive) to cool (dead)
        hue = py5.remap(self.health, 1.0, 0.0, 20, 220)
        sat = py5.remap(self.health, 1.0, 0.0, 80, 40)
        bright = py5.remap(self.health, 1.0, 0.0, 90, 60)
        alpha = py5.remap(self.health, 1.0, 0.0, 90, 40)
        
        py5.fill(hue, sat, bright, alpha)
        
        # Stroke slowly fades out
        py5.stroke(hue, sat, 100, alpha * 0.8)
        py5.stroke_weight(2 / scale) # Keep stroke visually consistent
        
        py5.begin_shape()
        for v in self.vertices:
            py5.vertex(v[0], v[1])
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

fragments = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Generate points for Delaunay triangulation to make a pseudo-Voronoi mesh
    points = []
    for _ in range(800):
        # Cluster mostly in the center
        r = py5.random(0, SIZE[0]/2 - 100)
        theta = py5.random(py5.TWO_PI)
        x = SIZE[0]/2 + r * py5.cos(theta)
        y = SIZE[1]/2 + r * py5.sin(theta)
        points.append([x, y])
        
    points = np.array(points)
    tri = Delaunay(points)
    
    # For each triangle, we make a Fragment
    for simplex in tri.simplices:
        p1, p2, p3 = points[simplex]
        
        # Calculate centroid
        centroid = (p1 + p2 + p3) / 3.0
        
        # Calculate relative vertices
        v1 = p1 - centroid
        v2 = p2 - centroid
        v3 = p3 - centroid
        
        fragments.append(Fragment(centroid, [v1, v2, v3]))

def draw():
    py5.background(0, 0, 5) # Dark background
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.blend_mode(py5.ADD)
    
    for f in fragments:
        f.update(t)
        f.draw(t)

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
