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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_PARTICLES = 500000

# State
points = np.zeros((NUM_PARTICLES, 2))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize randomly
    points[:, 0] = np.random.uniform(-2, 2, NUM_PARTICLES)
    points[:, 1] = np.random.uniform(-2, 2, NUM_PARTICLES)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10) # very dark trail to leave long smoky traces
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Base Clifford parameters (Pick some that look nice)
    base_a = 1.4
    base_b = 1.9
    base_c = 1.2
    base_d = 0.8
    
    # Mutate parameters to create organic kinetic morphing
    a = base_a + np.sin(t * 0.8) * 0.3
    b = base_b + np.cos(t * 1.1) * 0.3
    c = base_c + np.sin(t * 0.5) * 0.2
    d = base_d + np.cos(t * 0.7) * 0.4
    
    # Evaluate the map a few times per frame
    for _ in range(2):
        x = points[:, 0]
        y = points[:, 1]
        
        nx = np.sin(a * y) + c * np.cos(a * x)
        ny = np.sin(b * x) + d * np.cos(b * y)
        
        points[:, 0] = nx
        points[:, 1] = ny

    # Scale and center
    # The attractor naturally stays roughly within [-3, 3] depending on parameters
    scale = SIZE[1] * 0.22
    
    x2d = points[:, 0] * scale + SIZE[0]/2
    y2d = SIZE[1]/2 - points[:, 1] * scale
    
    # Coloring based on the speed / position
    # Let's segment by the value of x + y
    val = points[:, 0] + points[:, 1]
    
    mask_c1 = val > 1.0
    mask_c2 = (val <= 1.0) & (val > -1.0)
    mask_c3 = val <= -1.0
    
    py5.stroke_weight(1.5)
    
    # We use very low alpha so the overlapping points build up beautiful glowing textures
    
    # Cyan
    if np.any(mask_c1):
        py5.stroke(0, 255, 200, 10)
        pts = np.column_stack((x2d[mask_c1], y2d[mask_c1]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Magenta
    if np.any(mask_c2):
        py5.stroke(255, 0, 150, 10)
        pts = np.column_stack((x2d[mask_c2], y2d[mask_c2]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Gold
    if np.any(mask_c3):
        py5.stroke(255, 200, 0, 10)
        pts = np.column_stack((x2d[mask_c3], y2d[mask_c3]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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
        import os
        os._exit(0)

py5.run_sketch()
