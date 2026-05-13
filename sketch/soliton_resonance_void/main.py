from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

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

# Simulation Parameters (2D NLSE)
GRID_SIZE = 256
DT = 0.1
DX = 1.0
NONLINEARITY = 0.8
DAMPING = 0.999

# State
psi = None

def setup():
    global psi
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize psi with multiple Gaussian pulses (solitons)
    x = np.linspace(-GRID_SIZE/2, GRID_SIZE/2, GRID_SIZE)
    y = np.linspace(-GRID_SIZE/2, GRID_SIZE/2, GRID_SIZE)
    X, Y = np.meshgrid(x, y)
    
    psi = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.complex128)
    
    # Add solitons with initial velocities
    def add_soliton(cx, cy, kx, ky, amp):
        global psi
        dist_sq = (X - cx)**2 + (Y - cy)**2
        phase = kx * X + ky * Y
        psi += amp * np.exp(-dist_sq / 100.0) * np.exp(1j * phase)
        
    add_soliton(-50, -50, 1.0, 1.0, 2.0)
    add_soliton(50, 50, -1.0, -1.0, 2.0)
    add_soliton(-50, 50, 1.0, -1.0, 1.5)
    add_soliton(50, -50, -1.0, 1.0, 1.5)

def draw():
    global psi
    py5.background(10, 0, 20) # Deep Violet
    
    # 1. NLSE Update (Split-Step Fourier Method)
    # 1.1 Non-linear step (half step)
    psi *= np.exp(0.5j * NONLINEARITY * np.abs(psi)**2 * DT)
    
    # 1.2 Dispersion step (full step in Fourier space)
    psi_k = np.fft.fft2(psi)
    # k vectors
    kx = np.fft.fftfreq(GRID_SIZE, DX) * 2 * np.pi
    ky = np.fft.fftfreq(GRID_SIZE, DX) * 2 * np.pi
    KX, KY = np.meshgrid(kx, ky)
    K2 = KX**2 + KY**2
    psi_k *= np.exp(-0.5j * K2 * DT)
    psi = np.fft.ifft2(psi_k)
    
    # 1.3 Non-linear step (half step)
    psi *= np.exp(0.5j * NONLINEARITY * np.abs(psi)**2 * DT)
    
    psi *= DAMPING
    
    intensity = np.abs(psi)**2
    
    # 2. Rendering
    py5.no_stroke()
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2, -200)
    py5.rotate_x(py5.PI/3)
    py5.rotate_z(py5.frame_count * 0.01)
    
    scale = 6.0
    h_scale = 30.0
    
    # Draw as a grid of points or quads
    # We'll use a subsampled grid for performance
    STEP = 2
    for i in range(0, GRID_SIZE - STEP, STEP):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(0, GRID_SIZE, STEP):
            for k in [i, i + STEP]:
                h = intensity[k, j] * h_scale
                # Palette: Violet -> Rose -> Gold
                # Based on height
                norm_h = py5.constrain(intensity[k, j], 0, 5) / 5.0
                r = py5.lerp(100, 255, norm_h)
                g = py5.lerp(0, 150, norm_h)
                b = py5.lerp(255, 0, norm_h)
                
                py5.fill(r, g, b, 200)
                py5.vertex((j - GRID_SIZE/2) * scale, (k - GRID_SIZE/2) * scale, h)
        py5.end_shape()
        
    py5.pop_matrix()

    # 3. Save Frame and Video Export
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
