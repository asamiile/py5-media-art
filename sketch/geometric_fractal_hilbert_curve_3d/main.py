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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_POINTS = 8000
points = []

def setup():
    global points
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate 3D lattice random walk (Circuitry)
    curr = np.array([0.0, 0.0, 0.0])
    points.append(curr.copy())
    
    # To keep it centered and bounded, we bias the walk toward the center
    for _ in range(NUM_POINTS):
        axis = np.random.randint(0, 3)
        direction = 1 if np.random.rand() > 0.5 else -1
        
        # Bias toward center if getting too far
        if abs(curr[axis] + direction * 15) > 400:
            direction *= -1
            
        step = np.zeros(3)
        step[axis] = direction * 15
        curr += step
        points.append(curr.copy())
        
    points = np.array(points)

def draw():
    py5.background(10, 80, 10) # dark background
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Camera rotation
    rot_y = t * py5.TWO_PI
    rot_x = py5.sin(t * py5.TWO_PI) * 0.5
    py5.rotate_y(rot_y)
    py5.rotate_x(rot_x)
    
    # Morphing parameter:
    # Expands to 1 at mid, then back to 0.01
    expansion = py5.sin(t * py5.PI)
    
    py5.scale(expansion * 1.5 + 0.01)
    
    py5.no_fill()
    py5.stroke_weight(2)
    py5.blend_mode(py5.ADD)
    
    # Draw the circuit path
    py5.begin_shape(py5.LINE_STRIP)
    for i, pt in enumerate(points):
        # Color gradient based on position in path
        hue = (i / NUM_POINTS * 360 + t * 360 * 2) % 360
        py5.stroke(hue, 80, 100, 150)
        
        # Add some noise to the points for an energetic electric feel
        noise_x = py5.random(-2, 2) * expansion
        noise_y = py5.random(-2, 2) * expansion
        noise_z = py5.random(-2, 2) * expansion
        
        py5.vertex(pt[0] + noise_x, pt[1] + noise_y, pt[2] + noise_z)
    py5.end_shape()
    
    py5.pop_matrix()

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
