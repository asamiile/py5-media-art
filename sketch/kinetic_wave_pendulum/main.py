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

NUM_PENDULUMS = 45
GRAVITY = 9.81
MAX_LENGTH = 800
MIN_LENGTH = 300

# We want the pendulums to execute a specific number of oscillations in 15 seconds.
# For example, pendulum 0 executes 25 oscillations, pendulum 1 executes 26, etc.
# Period T = 2 * pi * sqrt(L/G)  => L = G * (T / (2*pi))^2
# T = Total Time / Number of oscillations
total_time = DURATION_SEC
oscillations = np.linspace(15, 30, NUM_PENDULUMS)
periods = total_time / oscillations
lengths = GRAVITY * (periods / (2 * np.pi))**2

# We scale the lengths so they fit on screen nicely
scale_factor = MAX_LENGTH / np.max(lengths)
lengths *= scale_factor * 50 # adjust for visual pixel scale

# Initial angle for all pendulums
theta_max = py5.PI / 4

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count / FPS
    
    py5.translate(py5.width / 2, 100, -500)
    
    # Slow cinematic camera rotation
    py5.rotate_y(py5.sin(t * 0.2) * 0.8)
    py5.rotate_x(-py5.PI / 12)
    
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 0, 1, -1)
    py5.directional_light(200, 100, 80, 1, -1, 1)
    
    spacing = 30
    start_z = -(NUM_PENDULUMS * spacing) / 2
    
    # Draw the support bar
    py5.stroke(0, 0, 80)
    py5.stroke_weight(5)
    py5.line(0, 0, start_z - spacing, 0, 0, start_z + NUM_PENDULUMS * spacing)
    
    py5.stroke_weight(2)
    py5.sphere_detail(20)
    
    for i in range(NUM_PENDULUMS):
        L = lengths[i]
        
        # Calculate current angle
        # Simple harmonic motion approximation (valid for small angles, but looks fine here)
        # theta(t) = theta_max * cos(sqrt(G/L) * t)
        # Using the scaled L requires adjusting G effectively, or we can just use the periods directly:
        omega = 2 * np.pi / periods[i]
        theta = theta_max * np.cos(omega * t)
        
        z = start_z + i * spacing
        x = L * np.sin(theta)
        y = L * np.cos(theta)
        
        # Draw string
        py5.stroke(0, 0, 50, 80)
        py5.line(0, 0, z, x, y, z)
        
        # Draw pendulum bob
        py5.push_matrix()
        py5.translate(x, y, z)
        
        hue = py5.remap(i, 0, NUM_PENDULUMS, 0, 360)
        py5.fill(hue, 90, 100)
        py5.no_stroke()
        py5.sphere(12)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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
