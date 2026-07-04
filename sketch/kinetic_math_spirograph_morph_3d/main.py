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

NUM_POINTS = 50000
u = np.linspace(0, 2 * np.pi, NUM_POINTS)

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(0, 0, 5) # Dark background
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Base frequencies for the 3D Fourier series knot
    # Higher primes create very dense, structured spirograph patterns
    fx1, fx2, fx3 = 11, 41, 107
    fy1, fy2, fy3 = 13, 43, 109
    fz1, fz2, fz3 = 17, 47, 113
    
    # Amplitudes
    ax1, ax2, ax3 = 1.0, 0.4, 0.15
    ay1, ay2, ay3 = 1.0, 0.4, 0.15
    az1, az2, az3 = 1.0, 0.4, 0.15
    
    # Time-varying phase shifts make the spirograph morph and writhe continuously
    px1 = t * 2 * np.pi * 1.5
    px2 = np.sin(t * 2 * np.pi) * np.pi * 0.5
    px3 = t * 2 * np.pi * 3
    
    py1 = t * 2 * np.pi * 2
    py2 = np.cos(t * 2 * np.pi) * np.pi * 0.5
    py3 = t * 2 * np.pi * 2.5
    
    pz1 = t * 2 * np.pi * 1
    pz2 = t * 2 * np.pi * 1.5
    pz3 = np.sin(t * 2 * np.pi + np.pi/4) * np.pi
    
    # Calculate 3D coordinates
    x = ax1 * np.sin(fx1 * u + px1) + ax2 * np.sin(fx2 * u + px2) + ax3 * np.sin(fx3 * u + px3)
    y = ay1 * np.sin(fy1 * u + py1) + ay2 * np.sin(fy2 * u + py2) + ay3 * np.sin(fy3 * u + py3)
    z = az1 * np.sin(fz1 * u + pz1) + az2 * np.sin(fz2 * u + pz2) + az3 * np.sin(fz3 * u + pz3)
    
    # Add a global rotation
    theta_y = t * 2 * np.pi
    theta_x = np.sin(t * 2 * np.pi) * 0.25
    
    cy, sy = np.cos(theta_y), np.sin(theta_y)
    cx, sx = np.cos(theta_x), np.sin(theta_x)
    
    pts_3d = np.column_stack((x, y, z))
    
    rot_y = np.array([
        [cy, 0, sy],
        [0, 1, 0],
        [-sy, 0, cy]
    ])
    
    rot_x = np.array([
        [1, 0, 0],
        [0, cx, -sx],
        [0, sx, cx]
    ])
    
    rotated = pts_3d @ rot_y.T @ rot_x.T
    
    # Manual Perspective Projection
    cam_dist = 4.0
    w = cam_dist / (cam_dist - rotated[:, 2])
    
    scale_factor = min(py5.width, py5.height) * 0.3
    
    x2d = py5.width / 2 + rotated[:, 0] * w * scale_factor
    y2d = py5.height / 2 + rotated[:, 1] * w * scale_factor
    
    projected = np.column_stack((x2d, y2d))
    
    # Calculate a hue that wraps around based on the parameter u
    hues = (u / (2 * np.pi) * 360 + t * 360 * 2) % 360
    
    # To create a glowing neon effect, we draw lines with additive blending
    py5.blend_mode(py5.ADD)
    
    # Convert points to flat array for faster py5 drawing
    # py5 vertex accepts x, y
    py5.no_fill()
    
    # Draw outer glow
    py5.stroke_weight(5.0)
    py5.begin_shape(py5.LINES)
    for i in range(NUM_POINTS - 1):
        py5.stroke(hues[i], 90, 100, 3)
        py5.vertex(projected[i, 0], projected[i, 1])
        py5.vertex(projected[i+1, 0], projected[i+1, 1])
    py5.end_shape()
    
    # Draw core line
    py5.stroke_weight(1.0)
    py5.begin_shape(py5.LINES)
    for i in range(NUM_POINTS - 1):
        py5.stroke(hues[i], 60, 100, 30)
        py5.vertex(projected[i, 0], projected[i, 1])
        py5.vertex(projected[i+1, 0], projected[i+1, 1])
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
