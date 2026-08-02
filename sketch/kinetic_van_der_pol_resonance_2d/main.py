from pathlib import Path
import sys
import random
import math
import subprocess
import shutil
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes
from lib.animation import frames_dir

# Directories and parameters
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

FPS = 60
TOTAL_FRAMES = 900  # 15 seconds
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Numerical parameters
N_RINGS = 5
N_OSC = 160  # Number of oscillators per ring
DT = 0.02
SUBSTEPS = 5

# Generative seed (ensures no fixed seeds)
SEED = random.randint(0, 1000000)
rng = np.random.RandomState(SEED)

# Oscillator parameters
angles = np.linspace(0, 2 * np.pi, N_OSC, endpoint=False)
base_r = np.array([240, 420, 600, 780, 960], dtype=np.float32).reshape(N_RINGS, 1)
mu = np.array([0.3, 0.7, 1.2, 1.8, 2.5], dtype=np.float32).reshape(N_RINGS, 1)

# State variables
x_state = rng.uniform(-0.5, 0.5, (N_RINGS, N_OSC)).astype(np.float32)
v_state = rng.uniform(-0.5, 0.5, (N_RINGS, N_OSC)).astype(np.float32)
t_time = 0.0

# Twinkling background stars
stars_x = np.zeros(800, dtype=np.float32)
stars_y = np.zeros(800, dtype=np.float32)
stars_phase = np.zeros(800, dtype=np.float32)

def setup():
    global stars_x, stars_y, stars_phase
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(280, 20, 5)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate background stars
    stars_x = rng.uniform(0, py5.width, 800)
    stars_y = rng.uniform(0, py5.height, 800)
    stars_phase = rng.uniform(0, np.pi * 2, 800)

def update_physics():
    global x_state, v_state, t_time
    
    # Modulate coupling and forcing over the 900 frame loop (t goes from 0 to 90.0)
    # forcing freq omega completes 15 cycles in 90.0 units of time
    omega = 15.0 * 2.0 * np.pi / 90.0
    
    # Modulation parameters
    progress = (py5.frame_count - 1) / TOTAL_FRAMES
    theta_mod = 2.0 * np.pi * progress
    
    # F_strength goes 0.0 -> 0.6 -> 0.0
    forcing_strength = 0.6 * 0.5 * (1.0 + np.sin(theta_mod - np.pi / 2.0))
    # C_strength goes 0.25 -> 0.0 -> 0.25
    coupling_strength = 0.25 * 0.5 * (1.0 + np.cos(theta_mod))
    
    # Multi-step Euler-Cromer integration for stability
    for _ in range(SUBSTEPS):
        # 1. Neighbor Coupling
        left_x = np.roll(x_state, 1, axis=1)
        right_x = np.roll(x_state, -1, axis=1)
        coupling = coupling_strength * (left_x + right_x - 2.0 * x_state)
        
        # 2. Spatially rotating forcing field (3-armed wave)
        forcing = forcing_strength * np.cos(omega * t_time - 3.0 * angles)
        
        # 3. Van der Pol acceleration
        # d2x/dt2 = mu*(1 - x^2)*dx/dt - x + coupling + forcing
        accel = mu * (1.0 - x_state**2) * v_state - x_state + coupling + forcing
        
        # Update
        v_state += accel * DT
        x_state += v_state * DT
        t_time += DT

def draw():
    # Clear screen with translucent fill to create motion blur trails
    py5.fill(280, 20, 5, 18)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw background stars
    for i in range(800):
        brightness = 40 + 35 * np.sin(py5.frame_count * 0.04 + stars_phase[i])
        py5.stroke(240, 15, brightness, 150)
        py5.stroke_weight(rng.uniform(0.8, 2.2))
        py5.point(stars_x[i], stars_y[i])
        
    # Update state
    update_physics()
    
    cx, cy = py5.width / 2.0, py5.height / 2.0
    
    # Draw loops and particles
    # Ring color mapping
    ring_hues = [150, 240, 290, 330, 30]
    ring_sats = [80, 80, 75, 85, 90]
    
    for k in range(N_RINGS):
        hue = ring_hues[k]
        sat = ring_sats[k]
        
        # Calculate screen coordinates for the entire ring
        r_current = base_r[k] + x_state[k] * 65.0
        px = cx + r_current * np.cos(angles)
        py = cy + r_current * np.sin(angles)
        
        # 1. Glow pass 1 (thicker, faint)
        py5.no_fill()
        py5.stroke(hue, sat, 90, 8)
        py5.stroke_weight(12.0)
        py5.begin_shape()
        for i in range(N_OSC):
            py5.vertex(px[i], py[i])
        py5.end_shape(py5.CLOSE)
        
        # 2. Glow pass 2 (medium)
        py5.stroke(hue, sat, 95, 25)
        py5.stroke_weight(5.0)
        py5.begin_shape()
        for i in range(N_OSC):
            py5.vertex(px[i], py[i])
        py5.end_shape(py5.CLOSE)
        
        # 3. Core pass (sharp, bright)
        py5.stroke(hue, max(0, sat - 15), 100, 85)
        py5.stroke_weight(1.5)
        py5.begin_shape()
        for i in range(N_OSC):
            py5.vertex(px[i], py[i])
        py5.end_shape(py5.CLOSE)
        
        # 4. Draw individual oscillator dots for added texture
        # To avoid overhead of N_OSC point calls, we group and draw them
        coords = np.stack([px, py], axis=1)
        
        # Glow dots
        py5.stroke(hue, sat, 95, 20)
        py5.stroke_weight(8.0)
        py5.points(coords)
        
        # Core dots
        py5.stroke(hue, max(0, sat - 20), 100, 90)
        py5.stroke_weight(2.5)
        py5.points(coords)

    # Fail-safe: check standard deviation to prevent blank frames
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress indicator
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    # Compile video on last frame
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot at mid-point
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Cleanup temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
