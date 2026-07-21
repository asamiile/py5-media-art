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

# KS equation simulation parameters
N = 1024 # Grid points in x
L = 100.0 # Domain length
dt = 0.05
dx = L / N

x = np.linspace(0, L, N)
# Initial condition: small random noise
u = np.random.uniform(-0.1, 0.1, N)

# We use an explicit finite difference scheme. For stability of higher order derivatives, 
# spectral methods (FFT) are usually better, but we will use a pseudo-spectral approach.
# In Fourier space, derivatives are just multiplications.

# Wavenumbers
k = np.fft.fftfreq(N, d=dx/(2*np.pi))

# Linear term in Fourier space: L = k^2 - k^4 (negative means stable, positive means unstable)
L_k = (k**2) - (k**4)

# ETD1 factors
E = np.exp(L_k * dt)
E_minus_1_over_L = np.zeros_like(L_k)
# Avoid division by zero at k=0
E_minus_1_over_L[L_k != 0] = (E[L_k != 0] - 1.0) / L_k[L_k != 0]
E_minus_1_over_L[L_k == 0] = dt

# We keep a history of the state to draw it as a 2D surface over time (y-axis)
HISTORY_ROWS = 600
history = np.zeros((HISTORY_ROWS, N), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global u, history
    
    # We step the simulation multiple times per frame
    for _ in range(3):
        u_hat = np.fft.fft(u)
        
        # Nonlinear term: F(u^2)
        u2_hat = np.fft.fft(u**2)
        N_hat = -0.5 * 1j * k * u2_hat
        
        # ETD1 step
        u_hat_next = E * u_hat + E_minus_1_over_L * N_hat
        
        u = np.real(np.fft.ifft(u_hat_next))
    
    # Shift history down and insert new row
    history[1:] = history[:-1]
    history[0] = u
    
    # Render
    py5.background(0)
    
    # Map to screen
    cell_w = py5.width / N
    cell_h = py5.height / HISTORY_ROWS
    
    py5.no_fill()
    py5.stroke_weight(cell_h + 1)
    
    for row in range(0, HISTORY_ROWS, 2): # Draw every other row for speed
        py5.begin_shape(py5.LINES)
        for col in range(N - 1):
            val = history[row, col]
            # Color map:
            # - High values (peaks) are bright yellow/white (hue 60)
            # - Medium values are orange (hue 30)
            # - Low values (troughs) are deep red (hue 0) or black
            
            normalized_val = (val + 3.0) / 6.0 # approximate bounds [-3, 3]
            normalized_val = np.clip(normalized_val, 0.0, 1.0)
            
            hue = normalized_val * 60
            sat = 100
            br = normalized_val * 100
            
            if br > 10:
                py5.stroke(hue, sat, br)
                py5.vertex(col * cell_w, row * cell_h)
                py5.vertex((col + 1) * cell_w, row * cell_h)
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
