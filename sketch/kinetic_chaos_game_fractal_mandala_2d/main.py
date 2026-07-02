import os
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
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Chaos Game Setup
N_POINTS = 300000
N_VERTICES = 6
JUMP_FACTOR = 0.5  # Standard for Sierpinski

# We keep the state of points persistent across frames
points = np.zeros((N_POINTS, 2))
colors = np.zeros((N_POINTS, 3))

# Define colors for the 6 vertices (Bioluminescent Teal, Purple, Pink, Green, Blue, Cyan)
vertex_colors = np.array([
    [0, 255, 200],   # Teal
    [150, 0, 255],   # Purple
    [255, 0, 150],   # Pink
    [0, 255, 100],   # Green
    [0, 100, 255],   # Blue
    [0, 255, 255]    # Cyan
])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    
    # Initialize random starting points near the center
    points[:, 0] = np.random.uniform(SIZE[0]/2 - 100, SIZE[0]/2 + 100, N_POINTS)
    points[:, 1] = np.random.uniform(SIZE[1]/2 - 100, SIZE[1]/2 + 100, N_POINTS)

def draw():
    # We clear the background each frame, drawing the current state of the fractal
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES * 2 * np.pi
    
    # Calculate the positions of the 6 attractor vertices
    # They form a hexagon that breathes and rotates
    base_radius = py5.height * 0.45
    breathe = 1.0 + 0.15 * np.sin(t * 3)
    radius = base_radius * breathe
    rotation = t
    
    angles = np.linspace(0, 2*np.pi, N_VERTICES, endpoint=False) + rotation
    vertices = np.empty((N_VERTICES, 2))
    vertices[:, 0] = SIZE[0]/2 + np.cos(angles) * radius
    vertices[:, 1] = SIZE[1]/2 + np.sin(angles) * radius
    
    # Perform a few iterations of the chaos game per frame to quickly settle points 
    # onto the new attractor positions
    for _ in range(5):
        # Pick random vertices for each point
        choices = np.random.randint(0, N_VERTICES, N_POINTS)
        target_vertices = vertices[choices]
        
        # Jump halfway to the chosen vertex
        points[:] = points + (target_vertices - points) * JUMP_FACTOR
        
        # Interpolate color towards the chosen vertex color to create gradients
        colors[:] = colors * 0.8 + vertex_colors[choices] * 0.2
        
    # Draw all points
    py5.stroke_weight(1.5)
    
    # It is faster to draw points using a vectorized approach in py5
    # Since py5.points() doesn't take colors directly, we will draw them in groups by dominant color
    # For a glowing effect, we just use a generic bioluminescent cyan color and map alpha
    # But for full color we can chunk them by choice (the last chosen vertex)
    for i in range(N_VERTICES):
        mask = choices == i
        pts = points[mask]
        c = vertex_colors[i]
        py5.stroke(c[0], c[1], c[2], 100)
        py5.points(pts)

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
        
        import os
        os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
