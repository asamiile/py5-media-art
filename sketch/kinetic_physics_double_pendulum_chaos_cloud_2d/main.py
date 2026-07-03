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

N = 25000
# Parameters for double pendulum
g = 9.81
L1 = 400.0
L2 = 400.0
m1 = 10.0
m2 = 10.0

# Initial conditions: all start at almost the same angle, with infinitesimal differences
theta1 = np.full(N, np.pi / 2.0)
# Spread theta2 by a tiny amount
theta2 = np.full(N, np.pi / 2.0) + np.linspace(-0.0001, 0.0001, N)

omega1 = np.zeros(N)
omega2 = np.zeros(N)

dt = 0.1

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 15)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_fill()
    py5.stroke_weight(1.5)

def update_pendulums():
    global theta1, theta2, omega1, omega2
    
    # We use a semi-implicit Euler or standard equations of motion for a double pendulum
    # Equations of motion:
    delta = theta2 - theta1
    
    den1 = (m1 + m2) * L1 - m2 * L1 * np.cos(delta) * np.cos(delta)
    alpha1 = (m2 * L1 * omega1 * omega1 * np.sin(delta) * np.cos(delta)
              + m2 * g * np.sin(theta2) * np.cos(delta)
              + m2 * L2 * omega2 * omega2 * np.sin(delta)
              - (m1 + m2) * g * np.sin(theta1)) / den1
              
    den2 = (L2 / L1) * den1
    alpha2 = (-m2 * L2 * omega2 * omega2 * np.sin(delta) * np.cos(delta)
              + (m1 + m2) * g * np.sin(theta1) * np.cos(delta)
              - (m1 + m2) * L1 * omega1 * omega1 * np.sin(delta)
              - (m1 + m2) * g * np.sin(theta2)) / den2
              
    omega1 += alpha1 * dt
    omega2 += alpha2 * dt
    theta1 += omega1 * dt
    theta2 += omega2 * dt

def draw():
    global theta1, theta2, omega1, omega2
    
    # Slight fade for motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 8)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Update physics multiple times per frame for speed
    for _ in range(3):
        update_pendulums()
        
    x1 = py5.width / 2 + L1 * np.sin(theta1)
    y1 = py5.height / 2 + L1 * np.cos(theta1)
    
    x2 = x1 + L2 * np.sin(theta2)
    y2 = y1 + L2 * np.cos(theta2)
    
    # Draw points for the second mass
    hue_vals = (np.linspace(180, 320, N) + py5.frame_count * 0.5) % 360
    
    # To draw fast, we can use py5.points() if we pass an array, or iterate.
    # Py5 allows setting stroke for all points if we draw them as one big shape?
    # Actually, we can draw a set of points. But we want colored points.
    # The fastest way in py5 to draw colored points is to group them by color,
    # or just iterate (it's fast enough for 25k).
    
    # Fast path: Group points into bins of colors
    num_bins = 60
    bin_size = N // num_bins
    
    py5.stroke_weight(2.0)
    for b in range(num_bins):
        start = b * bin_size
        end = start + bin_size
        h = hue_vals[start]
        py5.stroke(h, 80, 80, 15)
        
        pts = np.column_stack((x2[start:end], y2[start:end]))
        py5.points(pts)

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
