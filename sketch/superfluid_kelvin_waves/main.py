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
NUM_FILAMENTS = 12
PARTICLES_PER_FILAMENT = 10_000
NUM_PARTICLES = NUM_FILAMENTS * PARTICLES_PER_FILAMENT
NUM_STARS = 10_000

# State
u_vals = None
filament_centers = None
filament_radii = None
stars = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global u_vals, filament_centers, filament_radii, stars
    
    # Pre-compute parameter u [0, 2pi] for each particle
    u_vals = np.tile(np.linspace(0, 2 * np.pi, PARTICLES_PER_FILAMENT), NUM_FILAMENTS).astype(np.float32)
    
    # Filament properties
    filament_centers = np.random.uniform(-100, 100, (NUM_FILAMENTS, 3)).astype(np.float32)
    filament_radii = np.random.uniform(150, 300, NUM_FILAMENTS).astype(np.float32)
    
    # Background stars
    stars = np.random.uniform(-1500, 1500, (NUM_STARS, 3)).astype(np.float32)

def draw():
    if py5.frame_count % 50 == 0:
        print(f"Frame: {py5.frame_count}/{TOTAL_FRAMES}")
    
    t = py5.frame_count * 0.02
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    py5.camera(600 * np.sin(t * 0.1), 400 * np.cos(t * 0.15), 600 * np.cos(t * 0.1),
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(255, 120)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Physics: Kelvin Waves on Vortex Filaments
    # Each filament i:
    # p = center_i + rotation_i * (base_circle + kelvin_waves)
    
    all_pts = []
    
    for i in range(NUM_FILAMENTS):
        u = u_vals[i * PARTICLES_PER_FILAMENT : (i+1) * PARTICLES_PER_FILAMENT]
        r = filament_radii[i]
        c = filament_centers[i]
        
        # Base circle
        x = r * np.cos(u)
        y = r * np.sin(u)
        z = np.zeros_like(u)
        
        # Kelvin Waves (multi-octave helical ripples)
        # Octave 1
        n1 = 4.0
        amp1 = 20.0 * np.sin(t * 0.5 + i)
        x += amp1 * np.cos(n1 * u + t * 2.0)
        z += amp1 * np.sin(n1 * u + t * 2.0)
        
        # Octave 2
        n2 = 12.0
        amp2 = 8.0 * np.cos(t * 0.8 - i)
        y += amp2 * np.sin(n2 * u - t * 3.0)
        z += amp2 * np.cos(n2 * u - t * 3.0)
        
        # Rotation for orientation
        rot_t = t * 0.1 + i * 1.5
        rx = x * np.cos(rot_t) - z * np.sin(rot_t)
        rz = x * np.sin(rot_t) + z * np.cos(rot_t)
        
        all_pts.append(np.stack([rx + c[0], y + c[1], rz + c[2]], axis=-1))
    
    all_pts = np.concatenate(all_pts, axis=0).astype(np.float32)
    
    # Additive Rendering
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Draw filaments
    for i in range(NUM_FILAMENTS):
        pts = all_pts[i * PARTICLES_PER_FILAMENT : (i+1) * PARTICLES_PER_FILAMENT]
        
        # Color based on filament index and local curvature proxy (Z-variation)
        # Teal (170) and Violet (270)
        h = 170 if i % 2 == 0 else 270
        s = 80
        b = 100
        
        # Vectorized segments or points
        py5.stroke(h, s, b, 60)
        py5.stroke_weight(1.2)
        py5.points(pts)
        
        # Core highlights
        py5.stroke(0, 0, 100, 40)
        py5.stroke_weight(0.5)
        py5.points(pts)

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
