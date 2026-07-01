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
NUM_PARTICLES = 300000

# State
points = np.zeros((NUM_PARTICLES, 2))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize randomly
    # The attractor naturally clusters depending on initial points, 
    # but area-preserving maps usually look better when initialized with some symmetry
    radius = np.random.uniform(0.1, 15.0, NUM_PARTICLES)
    angle = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    
    points[:, 0] = radius * np.cos(angle)
    points[:, 1] = radius * np.sin(angle)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 0, 10, 10) # very dark purple/black with low opacity for smoky trails
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # Gumowski-Mira parameters
    # The 'a' parameter dramatically changes the shape.
    # We mutate it slowly to create organic breathing/morphing
    # Typical range is [-0.9, 0.9]. We will oscillate between -0.4 and 0.4
    a = np.sin(t * 0.5) * 0.4
    
    # 'b' usually set to 1 for area-preserving
    # If we drift it slightly it might collapse, so we keep b = 1.0 but maybe add a tiny friction/expansion
    b = 1.0
    
    # f(x) = a*x + 2*(1-a)*x^2 / (1+x^2)
    # The classic formulation is f(x) = a*x + (2*(1-a)*x^2)/(1+x^2)
    # Another variant: f(x) = a*x + (1-a)*x^2 * exp(-x^2/4) or similar.
    # We use the classic one:
    
    def f(x, a):
        return a * x + (2 * (1 - a) * x**2) / (1 + x**2)

    # Evaluate the map a few times per frame
    for _ in range(2):
        x = points[:, 0]
        y = points[:, 1]
        
        # Gumowski-Mira equations
        # x_{n+1} = b y_n + f(x_n)
        # y_{n+1} = -x_n + f(x_{n+1})
        
        nx = b * y + f(x, a)
        ny = -x + f(nx, a)
        
        points[:, 0] = nx
        points[:, 1] = ny

    # Scale and center
    # The bounds of the attractor change depending on initial conditions and `a`
    # We use a fixed scale that usually fits well
    scale = SIZE[1] * 0.035
    
    x2d = points[:, 0] * scale + SIZE[0]/2
    y2d = SIZE[1]/2 - points[:, 1] * scale
    
    # Color mapping
    # We'll assign colors based on the polar angle of the particle's position
    # This creates a radial rainbow/gradient effect
    angles = np.arctan2(points[:, 1], points[:, 0])
    
    mask_c1 = (angles > -np.pi/3) & (angles <= np.pi/3) # Right
    mask_c2 = (angles > np.pi/3) & (angles <= np.pi)    # Top/Left
    mask_c3 = (angles > -np.pi) & (angles <= -np.pi/3)  # Bottom/Left
    
    py5.stroke_weight(1.5)
    
    # Red/Orange
    if np.any(mask_c1):
        py5.stroke(255, 100, 50, 15)
        pts = np.column_stack((x2d[mask_c1], y2d[mask_c1]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Blue/Cyan
    if np.any(mask_c2):
        py5.stroke(50, 200, 255, 15)
        pts = np.column_stack((x2d[mask_c2], y2d[mask_c2]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Purple/Magenta
    if np.any(mask_c3):
        py5.stroke(200, 50, 255, 15)
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
