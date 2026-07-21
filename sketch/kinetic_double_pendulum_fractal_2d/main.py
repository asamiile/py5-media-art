from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PENDULUMS = 15000

# Constants
G = 9.81
L1 = 400.0
L2 = 400.0
M1 = 10.0
M2 = 10.0

# Initial conditions (all start horizontally but with tiny offsets)
theta1 = np.full(NUM_PENDULUMS, np.pi / 2, dtype=np.float32)
# theta2 gets the micro variation
theta2 = np.linspace(np.pi / 2, np.pi / 2 + 0.001, NUM_PENDULUMS, dtype=np.float32)

omega1 = np.zeros(NUM_PENDULUMS, dtype=np.float32)
omega2 = np.zeros(NUM_PENDULUMS, dtype=np.float32)

dt = 0.05

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)

def draw():
    global theta1, theta2, omega1, omega2
    
    # We clear the background partially with a rect to leave a trail
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Store old positions for line drawing
    old_x2 = py5.width / 2 + L1 * np.sin(theta1) + L2 * np.sin(theta2)
    old_y2 = py5.height / 2 - 200 + L1 * np.cos(theta1) + L2 * np.cos(theta2)
    
    # Several sub-steps for stability
    for _ in range(4):
        delta_theta = theta1 - theta2
        
        # Denominators
        den1 = (2 * M1 + M2 - M2 * np.cos(2 * theta1 - 2 * theta2))
        den2 = (L2 / L1) * den1
        
        # Numerators for alpha1 (angular acceleration 1)
        num1 = -G * (2 * M1 + M2) * np.sin(theta1)
        num2 = -M2 * G * np.sin(theta1 - 2 * theta2)
        num3 = -2 * np.sin(theta1 - theta2) * M2
        num4 = omega2**2 * L2 + omega1**2 * L1 * np.cos(theta1 - theta2)
        alpha1 = (num1 + num2 + num3 * num4) / (L1 * den1)
        
        # Numerators for alpha2
        num5 = 2 * np.sin(theta1 - theta2)
        num6 = omega1**2 * L1 * (M1 + M2)
        num7 = G * (M1 + M2) * np.cos(theta1)
        num8 = omega2**2 * L2 * M2 * np.cos(theta1 - theta2)
        alpha2 = (num5 * (num6 + num7 + num8)) / (L2 * den1)
        
        omega1 += alpha1 * dt
        omega2 += alpha2 * dt
        theta1 += omega1 * dt
        theta2 += omega2 * dt
        
        # Damping
        omega1 *= 0.999
        omega2 *= 0.999
        
    new_x2 = py5.width / 2 + L1 * np.sin(theta1) + L2 * np.sin(theta2)
    new_y2 = py5.height / 2 - 200 + L1 * np.cos(theta1) + L2 * np.cos(theta2)
    
    # Draw trails
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    
    # Color based on index
    hues = np.linspace(0, 360, NUM_PENDULUMS)
    
    for i in range(NUM_PENDULUMS):
        py5.stroke(hues[i], 90, 100, 30)
        py5.vertex(old_x2[i], old_y2[i])
        py5.vertex(new_x2[i], new_y2[i])
    py5.end_shape()

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
        import os
        os._exit(0)

py5.run_sketch()
