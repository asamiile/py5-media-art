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

# Data for tubes
num_tubes = 12
tubes = []

class FluxTube:
    def __init__(self):
        self.points = []
        self.hue = py5.random(0, 50) # Orange to yellow to red
        # Base anchor points on a central sphere
        r = 150
        ang1 = py5.random(py5.TWO_PI)
        phi1 = py5.random(py5.PI)
        self.p1 = np.array([r * py5.sin(phi1) * py5.cos(ang1), r * py5.sin(phi1) * py5.sin(ang1), r * py5.cos(phi1)])
        
        ang2 = py5.random(py5.TWO_PI)
        phi2 = py5.random(py5.PI)
        self.p2 = np.array([r * py5.sin(phi2) * py5.cos(ang2), r * py5.sin(phi2) * py5.sin(ang2), r * py5.cos(phi2)])
        
        # Control points outward
        self.cp1_len = py5.random(300, 800)
        self.cp2_len = py5.random(300, 800)
        
    def draw(self, t):
        # Animate control points
        cp1 = self.p1 + self.p1 / np.linalg.norm(self.p1) * self.cp1_len
        cp2 = self.p2 + self.p2 / np.linalg.norm(self.p2) * self.cp2_len
        
        # Add twist
        cp1_twist = np.array([
            py5.sin(t * 0.05 + self.p1[0]) * 200,
            py5.cos(t * 0.04 + self.p1[1]) * 200,
            py5.sin(t * 0.03 + self.p1[2]) * 200
        ])
        cp2_twist = np.array([
            py5.cos(t * 0.05 + self.p2[0]) * 200,
            py5.sin(t * 0.04 + self.p2[1]) * 200,
            py5.cos(t * 0.03 + self.p2[2]) * 200
        ])
        
        cp1 += cp1_twist
        cp2 += cp2_twist
        
        # Draw the bezier tube by drawing many bezier lines slightly offset
        py5.stroke(self.hue, 90, 100, 40)
        py5.no_fill()
        
        for i in range(10):
            py5.stroke_weight(py5.random(1, 5))
            offset = np.array([py5.random(-15, 15), py5.random(-15, 15), py5.random(-15, 15)])
            py5.bezier(
                self.p1[0] + offset[0], self.p1[1] + offset[1], self.p1[2] + offset[2],
                cp1[0] + offset[0], cp1[1] + offset[1], cp1[2] + offset[2],
                cp2[0] + offset[0], cp2[1] + offset[1], cp2[2] + offset[2],
                self.p2[0] + offset[0], self.p2[1] + offset[1], self.p2[2] + offset[2]
            )

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for _ in range(num_tubes):
        tubes.append(FluxTube())

def draw():
    py5.background(0, 0, 5) # Dark space
    
    py5.translate(py5.width/2, py5.height/2, -300)
    
    t = py5.frame_count
    py5.rotate_y(t * 0.01)
    py5.rotate_x(py5.sin(t * 0.005) * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    # Draw central "sun"
    py5.no_stroke()
    py5.fill(30, 90, 100, 20)
    py5.sphere_detail(30)
    py5.sphere(145)
    py5.fill(20, 90, 100, 80)
    py5.sphere(130)
    
    for tube in tubes:
        tube.draw(t)

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
