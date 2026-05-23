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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Render at half resolution for performance, then upscale
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2

# Double pendulum parameters
G = 9.81
L1 = 1.0
L2 = 1.0
M1 = 1.0
M2 = 1.0
DT = 0.05

# Initial state grids
# x axis maps to theta1 from -pi to pi
# y axis maps to theta2 from -pi to pi
x = np.linspace(-np.pi, np.pi, SIM_W, dtype=np.float32)
y = np.linspace(-np.pi, np.pi, SIM_H, dtype=np.float32)
xv, yv = np.meshgrid(x, y)

theta1 = xv.copy()
theta2 = yv.copy()
omega1 = np.zeros_like(theta1)
omega2 = np.zeros_like(theta2)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global theta1, theta2, omega1, omega2
    
    # Run multiple physics steps per frame
    for _ in range(4):
        # Equations of motion for double pendulum
        dtheta = theta1 - theta2
        
        den1 = (2*M1 + M2) - M2 * np.cos(2*theta1 - 2*theta2)
        den2 = (L2/L1) * den1
        
        num1 = -G * (2*M1 + M2) * np.sin(theta1) - M2 * G * np.sin(theta1 - 2*theta2) \
               - 2 * np.sin(dtheta) * M2 * (omega2**2 * L2 + omega1**2 * L1 * np.cos(dtheta))
               
        num2 = 2 * np.sin(dtheta) * (omega1**2 * L1 * (M1 + M2) \
               + G * (M1 + M2) * np.cos(theta1) \
               + omega2**2 * L2 * M2 * np.cos(dtheta))
               
        alpha1 = num1 / (L1 * den1)
        alpha2 = num2 / (L2 * den2)
        
        omega1 += alpha1 * DT
        omega2 += alpha2 * DT
        theta1 += omega1 * DT
        theta2 += omega2 * DT

    # Compute kinetic energy or angle for coloring
    # Let's map theta2 to a color wheel
    t2_wrapped = (theta2 + np.pi) % (2 * np.pi)
    
    # Simple HSB to RGB mapping using sin waves for high performance
    # Normalized 0 to 1
    hue = t2_wrapped / (2 * np.pi)
    
    r = (np.sin(hue * 2 * np.pi + 0) * 127 + 128).astype(np.uint8)
    g = (np.sin(hue * 2 * np.pi + 2 * np.pi / 3) * 127 + 128).astype(np.uint8)
    b = (np.sin(hue * 2 * np.pi + 4 * np.pi / 3) * 127 + 128).astype(np.uint8)
    
    # Upscale by 2x
    r_up = np.kron(r, np.ones((2, 2), dtype=np.uint8))
    g_up = np.kron(g, np.ones((2, 2), dtype=np.uint8))
    b_up = np.kron(b, np.ones((2, 2), dtype=np.uint8))
    
    r_up = r_up[:SIZE[1], :SIZE[0]]
    g_up = g_up[:SIZE[1], :SIZE[0]]
    b_up = b_up[:SIZE[1], :SIZE[0]]
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = r_up
    pixels[:, :, 2] = g_up
    pixels[:, :, 3] = b_up
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
