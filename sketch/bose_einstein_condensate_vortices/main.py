import numpy as np
import py5
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Grid parameters
GRID_W = 400
GRID_H = 400
CELL_SIZE = 4.0

x = np.linspace(-GRID_W/2, GRID_H/2, GRID_W, dtype=np.float32)
y = np.linspace(-GRID_H/2, GRID_H/2, GRID_H, dtype=np.float32)
X, Y = np.meshgrid(x, y)

NUM_VORTICES = 6
# [x, y, vx, vy, charge (+1 or -1)]
vortices = np.zeros((NUM_VORTICES, 5), dtype=np.float32)

pts = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
pts[:, :, 0] = X * CELL_SIZE
pts[:, :, 2] = Y * CELL_SIZE

colors = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    global vortices
    for i in range(NUM_VORTICES):
        vortices[i, 0] = np.random.uniform(-GRID_W/3, GRID_W/3)
        vortices[i, 1] = np.random.uniform(-GRID_H/3, GRID_H/3)
        # drift velocity
        angle = np.random.uniform(0, 2*np.pi)
        speed = np.random.uniform(0.1, 0.4)
        vortices[i, 2] = np.cos(angle) * speed
        vortices[i, 3] = np.sin(angle) * speed
        vortices[i, 4] = 1.0 if i % 2 == 0 else -1.0

def draw():
    global vortices, pts, colors
    
    py5.background(220, 100, 5)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 100, -200)
    py5.rotate_x(1.0)
    py5.rotate_z(py5.frame_count * 0.005)
    
    # Update vortices
    vortices[:, 0] += vortices[:, 2]
    vortices[:, 1] += vortices[:, 3]
    
    # Simple bounds checking to keep them somewhat contained
    mask_x = np.abs(vortices[:, 0]) > GRID_W/2
    vortices[mask_x, 2] *= -1
    mask_y = np.abs(vortices[:, 1]) > GRID_H/2
    vortices[mask_y, 3] *= -1
    
    # Calculate wave function phase and amplitude
    phase = np.zeros_like(X)
    amplitude = np.ones_like(X)
    
    # Add background density waves
    t = py5.frame_count * 0.05
    bg_wave = np.sin(X*0.05 + t) * np.cos(Y*0.05 + t*0.8)
    
    for i in range(NUM_VORTICES):
        dx = X - vortices[i, 0]
        dy = Y - vortices[i, 1]
        
        # Phase field (angle)
        phase += vortices[i, 4] * np.arctan2(dy, dx)
        
        # Amplitude drops near vortex core
        r = np.sqrt(dx**2 + dy**2)
        core_size = 15.0
        amplitude *= (1.0 - np.exp(-r**2 / core_size**2))
    
    # Final combined wave state
    wave_real = amplitude * np.cos(phase + bg_wave*2.0 - t*2.0)
    wave_imag = amplitude * np.sin(phase + bg_wave*2.0 - t*2.0)
    
    # Height is based on real part
    pts[:, :, 1] = wave_real * 80.0
    
    # Density determines brightness
    density = amplitude**2
    
    # Draw points
    py5.stroke_weight(2.0)
    
    # We flatten for fast rendering
    flat_pts = pts.reshape(-1, 3)
    flat_phase = phase.reshape(-1) % (2*np.pi)
    flat_density = density.reshape(-1)
    
    # Create mask for different colors based on phase and density
    c1_mask = (flat_phase < np.pi) & (flat_density > 0.3)
    c2_mask = (flat_phase >= np.pi) & (flat_density > 0.3)
    core_mask = flat_density <= 0.3
    
    if np.any(c1_mask):
        py5.stroke(190, 100, 80, 50)
        py5.points(flat_pts[c1_mask])
        
    if np.any(c2_mask):
        py5.stroke(230, 100, 90, 50)
        py5.points(flat_pts[c2_mask])
        
    if np.any(core_mask):
        py5.stroke(200, 20, 100, 80)
        py5.stroke_weight(4.0)
        py5.points(flat_pts[core_mask])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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

py5.run_sketch()
