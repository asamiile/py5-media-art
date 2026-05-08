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
NUM_PARTICLES = 150_000
NUM_STARS = 12_000

# State
particles = None
stars = None
colors = None
particle_life = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, stars, colors, particle_life
    
    # Initialize particles in a large volume
    particles = np.random.uniform(-400, 400, (NUM_PARTICLES, 3)).astype(np.float32)
    particle_life = np.random.uniform(0, 100, NUM_PARTICLES).astype(np.float32)
    
    # Random HSB colors (Cyan/Amethyst/Gold)
    choices = [
        (180, 85, 100),  # Cyan
        (280, 75, 100),  # Amethyst
        (45, 95, 100)    # Gold
    ]
    indices = np.random.choice(len(choices), NUM_PARTICLES)
    colors = np.array([choices[i] for i in indices], dtype=np.float32)
    
    # Background stars
    stars = np.random.uniform(-1200, 1200, (NUM_STARS, 3)).astype(np.float32)

def draw():
    global particles, particle_life
    if py5.frame_count % 50 == 0:
        print(f"Frame: {py5.frame_count}/{TOTAL_FRAMES}")
    t = py5.frame_count * 0.02
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera: Smooth orbital sweep
    cam_r = 700 + 100 * np.sin(t * 0.1)
    py5.camera(cam_r * np.sin(t * 0.15), 200 * np.cos(t * 0.2), cam_r * np.cos(t * 0.15),
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(255, 120)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Physics: Complex Singularity Braiding
    # Zeros (Z) and Poles (P) moving in harmonic orbits
    z1 = 180 * (np.cos(t * 0.8) + 1j * np.sin(t * 1.2))
    z2 = 180 * (np.cos(t * 1.1 + 0.5) + 1j * np.sin(t * 0.7))
    p1 = 120 * (np.cos(t * 1.5) + 1j * np.sin(t * 0.9))
    p2 = 120 * (np.cos(t * 0.6 + 1.2) + 1j * np.sin(t * 1.3))
    
    # Update particle life and recycle
    particle_life += 1.0
    dead_mask = (particle_life > 100) | (np.abs(particles[:, 0]) > 1000) | (np.abs(particles[:, 1]) > 1000)
    if np.any(dead_mask):
        particles[dead_mask] = np.random.uniform(-500, 500, (np.sum(dead_mask), 3))
        particle_life[dead_mask] = 0
    
    # Complex advection in XY plane
    z_pts = particles[:, 0] + 1j * particles[:, 1]
    eps = 1e-4
    
    # Potential: f(z) = (z-z1)(z-z2) / ((z-p1)(z-p2))
    num = (z_pts - z1) * (z_pts - z2)
    den = (z_pts - p1) * (z_pts - p2) + eps
    f_z = num / den
    
    # Velocity v = conj(1/f_z) + rotational component
    v_field = np.conj(1.0 / (f_z + eps))
    v_rot = 1j * z_pts * 0.01  # Subtle global rotation
    
    v = (v_field * 8.0 + v_rot)
    
    particles[:, 0] += np.real(v).astype(np.float32)
    particles[:, 1] += np.imag(v).astype(np.float32)
    
    # Z-axis: Driven by field phase and a helical twist
    phase = np.angle(f_z)
    particles[:, 2] += np.sin(phase * 2.0 + t) * 3.0 + np.cos(t * 0.5) * 0.5
    
    # Bounding damping
    particles[:, 2] *= 0.98
    
    # Additive Rendering
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Draw particles in colored groups for performance
    hues = [180, 280, 45]
    for h in hues:
        mask = (colors[:, 0] == h) & (~dead_mask)
        if np.any(mask):
            # Alpha based on life (fade in/out)
            life_norm = particle_life[mask] / 100.0
            alphas = 70 * np.sin(np.pi * life_norm)
            
            # Binning alpha for performance
            for i in range(4):
                a_val = (i + 1) * 17
                bin_mask = (alphas >= i * 17) & (alphas < (i + 1) * 17)
                if np.any(bin_mask):
                    py5.stroke(h, colors[mask, 1][0], colors[mask, 2][0], float(a_val))
                    py5.stroke_weight(1.5)
                    py5.points(particles[mask][bin_mask])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Compress with libx264, yuv420p for compatibility
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Create preview from middle frame
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run([
            "cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        ], check=True)

if __name__ == "__main__":
    py5.run_sketch()
