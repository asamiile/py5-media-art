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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Crystal:
    def __init__(self, position, scale, rotation, color_hue, start_frame, duration):
        self.position = np.array(position, dtype=float)
        self.target_scale = scale
        self.rotation = np.array(rotation, dtype=float)
        self.hue = color_hue
        self.start_frame = start_frame
        self.duration = duration
        
    def draw(self, current_frame):
        if current_frame < self.start_frame:
            return
            
        progress = min(1.0, (current_frame - self.start_frame) / self.duration)
        # Ease out cubic
        progress = 1 - (1 - progress)**3
        
        if progress <= 0:
            return
            
        py5.push_matrix()
        py5.translate(*self.position)
        py5.rotate_x(self.rotation[0])
        py5.rotate_y(self.rotation[1])
        py5.rotate_z(self.rotation[2])
        py5.scale(self.target_scale * progress)
        
        py5.fill(self.hue, 80, 100, 40)
        py5.stroke((self.hue + 20) % 360, 60, 100, 80)
        py5.stroke_weight(2 / (self.target_scale * progress + 0.01))
        
        # Draw a custom faceted shape (octahedron)
        py5.begin_shape(py5.TRIANGLES)
        # Top half
        py5.vertex(0, 1, 0)
        py5.vertex(1, 0, 0)
        py5.vertex(0, 0, 1)
        
        py5.vertex(0, 1, 0)
        py5.vertex(0, 0, 1)
        py5.vertex(-1, 0, 0)
        
        py5.vertex(0, 1, 0)
        py5.vertex(-1, 0, 0)
        py5.vertex(0, 0, -1)
        
        py5.vertex(0, 1, 0)
        py5.vertex(0, 0, -1)
        py5.vertex(1, 0, 0)
        
        # Bottom half
        py5.vertex(0, -1, 0)
        py5.vertex(1, 0, 0)
        py5.vertex(0, 0, 1)
        
        py5.vertex(0, -1, 0)
        py5.vertex(0, 0, 1)
        py5.vertex(-1, 0, 0)
        
        py5.vertex(0, -1, 0)
        py5.vertex(-1, 0, 0)
        py5.vertex(0, 0, -1)
        
        py5.vertex(0, -1, 0)
        py5.vertex(0, 0, -1)
        py5.vertex(1, 0, 0)
        
        py5.end_shape()
        py5.pop_matrix()


crystals = []
active_crystals = []
seed_pos = [0, 0, 0]

# Generate crystal cluster recursively
def grow_crystals(pos, scale, hue, depth, start_frame):
    if depth > 4 or scale < 10:
        return
        
    duration = np.random.randint(30, 60)
    rot = np.random.uniform(0, py5.TWO_PI, 3)
    crystals.append(Crystal(pos, scale, rot, hue, start_frame, duration))
    
    # Spawn children
    num_children = np.random.randint(1, 4)
    for _ in range(num_children):
        child_dir = np.random.randn(3)
        child_dir /= np.linalg.norm(child_dir)
        child_pos = np.array(pos) + child_dir * scale * 0.8
        child_scale = scale * np.random.uniform(0.5, 0.8)
        child_hue = (hue + np.random.uniform(-30, 30)) % 360
        child_start = start_frame + np.random.randint(10, duration)
        
        if child_start < TOTAL_FRAMES * 0.8:
            grow_crystals(child_pos, child_scale, child_hue, depth + 1, child_start)

# Initialize growth
grow_crystals([0, 0, 0], 200, 200, 0, 0)


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)


def draw():
    py5.background(10, 20, 10)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Slow rotation
    angle = py5.TWO_PI * (py5.frame_count / TOTAL_FRAMES)
    py5.rotate_y(angle * 0.3)
    py5.rotate_x(py5.sin(angle * 0.5) * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    for c in crystals:
        c.draw(py5.frame_count)

    # Fail-safe

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
