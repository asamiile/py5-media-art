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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation constants
RES = 20  # 20^3 = 8,000 nodes
NUM_STARS = 10_000
SPACING = 30.0

# State
nodes_base = None
nodes_curr = None
stars = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes_base, nodes_curr, stars
    
    # Create 3D grid
    x, y, z = np.meshgrid(
        np.linspace(-(RES-1)*SPACING/2, (RES-1)*SPACING/2, RES),
        np.linspace(-(RES-1)*SPACING/2, (RES-1)*SPACING/2, RES),
        np.linspace(-(RES-1)*SPACING/2, (RES-1)*SPACING/2, RES)
    )
    nodes_base = np.stack([x, y, z], axis=-1).reshape(-1, 3).astype(np.float32)
    nodes_curr = nodes_base.copy()
    
    # Background stars
    stars = np.random.uniform(-1500, 1500, (NUM_STARS, 3)).astype(np.float32)

def draw():
    global nodes_curr
    if py5.frame_count % 50 == 0:
        print(f"Frame: {py5.frame_count}/{TOTAL_FRAMES}")
    
    t = py5.frame_count * 0.03
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    cam_r = 900 + 100 * np.cos(t * 0.2)
    py5.camera(cam_r * np.sin(t * 0.1), 300 * np.sin(t * 0.15), cam_r * np.cos(t * 0.1),
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(255, 150)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Physics: Volumetric Strain Field
    # Displacement = base + noise/sine deformation
    # Use a rotating "strain center"
    sc1 = 200 * np.array([np.sin(t * 0.7), np.cos(t * 0.5), np.sin(t * 0.3)])
    sc2 = 250 * np.array([np.cos(t * 0.4), np.sin(t * 0.6), np.cos(t * 0.8)])
    
    dist1 = np.linalg.norm(nodes_base - sc1, axis=1)
    dist2 = np.linalg.norm(nodes_base - sc2, axis=1)
    
    # Gaussian-like displacement
    disp = 60.0 * np.exp(-(dist1/150)**2)[:, np.newaxis] * (nodes_base - sc1) / (dist1[:, np.newaxis] + 1)
    disp += 50.0 * np.exp(-(dist2/200)**2)[:, np.newaxis] * (nodes_base - sc2) / (dist2[:, np.newaxis] + 1)
    
    # Add some harmonic vibration
    disp += 5.0 * np.sin(nodes_base * 0.05 + t)
    
    nodes_curr = nodes_base + disp
    
    # Calculate local "strain" as displacement magnitude
    strain = np.linalg.norm(disp, axis=1)
    max_strain = np.max(strain) if np.max(strain) > 0 else 1.0
    strain_norm = strain / 100.0  # Normalize for coloring
    
    # Additive Rendering
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Draw nodes in strain-based color bins
    # Low strain: Dark Cobalt/Teal
    # High strain: Bright Cyan/Magenta/Gold
    
    # We'll use 5 bins for strain
    for i in range(5):
        s_low = i * 0.2
        s_high = (i + 1) * 0.2
        mask = (strain_norm >= s_low) & (strain_norm < s_high)
        if np.any(mask):
            # Spectral shift: 180 (Cyan) -> 300 (Magenta) -> 45 (Gold)
            h = (180 + i * 30) % 360
            if i > 3: h = 45  # Gold for max strain
            
            s = 70 + i * 5
            b = 40 + i * 12
            alpha = 30 + i * 15
            
            py5.stroke(h, s, b, alpha)
            py5.stroke_weight(1.0 + i * 0.5)
            py5.points(nodes_curr[mask])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run([
            "cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        ], check=True)

if __name__ == "__main__":
    py5.run_sketch()
