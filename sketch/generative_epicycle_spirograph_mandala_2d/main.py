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
NUM_EPICYCLES = 120
SYMMETRY = 6

# Curve parameter t
t_curve = np.linspace(0, 2 * np.pi, NUM_POINTS, dtype=np.float32)

k_freqs = None
A_base = None
phi_base = None
speed_phi = None
noise_offsets = None

C1, C2, C3, C4 = None, None, None, None

def setup():
    global k_freqs, A_base, phi_base, speed_phi, noise_offsets, C1, C2, C3, C4
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize epicycles
    # For N-fold symmetry, k = N * m + 1
    m_vals = np.random.randint(-40, 40, NUM_EPICYCLES)
    k_freqs = (SYMMETRY * m_vals + 1).astype(np.float32)
    
    # Amplitudes decrease with higher frequencies for a smoother shape
    # But add some randomness
    A_base = np.random.uniform(10.0, 300.0, NUM_EPICYCLES) * (1.0 / (np.abs(m_vals) + 1.0)**0.8)
    phi_base = np.random.uniform(0, 2 * np.pi, NUM_EPICYCLES)
    speed_phi = np.random.uniform(-np.pi, np.pi, NUM_EPICYCLES) * 0.5
    noise_offsets = np.random.uniform(0, 1000, NUM_EPICYCLES)
    
    # Deep Void (#050505), Glowing Teal (#00E5FF), Electric Magenta (#FF00AA), Solar Gold (#FFD500)
    C1 = py5.color(5, 5, 5)
    C2 = py5.color(0, 229, 255)
    C3 = py5.color(255, 0, 170)
    C4 = py5.color(255, 213, 0)

def draw():
    py5.background(5, 5, 5) # Dark Void
    
    time_anim = py5.frame_count / TOTAL_FRAMES
    
    x = np.zeros(NUM_POINTS, dtype=np.float32)
    y = np.zeros(NUM_POINTS, dtype=np.float32)
    
    # Sum the epicycles
    for i in range(NUM_EPICYCLES):
        # Slowly varying amplitude
        n = py5.os_noise(noise_offsets[i], time_anim * 1.5)
        A = A_base[i] * (0.5 + 1.0 * n)
        
        # Slowly varying phase
        phi = phi_base[i] + speed_phi[i] * time_anim
        
        # Add to curve
        angle = k_freqs[i] * t_curve + phi
        x += A * np.cos(angle)
        y += A * np.sin(angle)
        
    # Center and scale to screen
    screen_x = py5.width / 2 + x * 2.5
    screen_y = py5.height / 2 + y * 2.5
    
    coords = np.column_stack((screen_x, screen_y))
    
    # Draw points in color bins along the curve (t_curve)
    num_bins = 20
    points_per_bin = NUM_POINTS // num_bins
    
    py5.stroke_weight(2)
    
    for i in range(num_bins):
        start_idx = i * points_per_bin
        end_idx = start_idx + points_per_bin
        
        # Color interpolation based on position along the curve (0 to 1)
        # We loop the color map twice to make it seamless
        f = (i / float(num_bins)) * 2.0
        if f > 1.0: f = 2.0 - f
        
        # Add a subtle time shift to the colors so they flow
        f = (f + time_anim) % 1.0
        
        if f < 0.33:
            c = py5.lerp_color(C2, C3, f / 0.33)
        elif f < 0.66:
            c = py5.lerp_color(C3, C4, (f - 0.33) / 0.33)
        else:
            c = py5.lerp_color(C4, C2, (f - 0.66) / 0.34)
            
        py5.stroke(c)
        py5.no_fill()
        
        # Connect to the previous segment by including end_idx + 1
        end = min(end_idx + 1, NUM_POINTS)
        chunk = coords[start_idx:end]
        
        py5.begin_shape()
        py5.vertices(chunk)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
