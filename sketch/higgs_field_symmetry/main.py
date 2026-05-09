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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 200_000
FIELD_SCALE = 150.0
DAMPING = 0.92
NOISE_STRENGTH = 0.5
TRANSITION_START = 5 * FPS
TRANSITION_END = 12 * FPS

# State
base_pos = None
field_state = None  # (N, 3)
field_vel = None    # (N, 3)
stars = None

def setup():
    global base_pos, field_state, field_vel, stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize base positions (spherical cloud)
    r = np.random.uniform(0, 400, NUM_PARTICLES)
    theta = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    phi = np.arccos(np.random.uniform(-1, 1, NUM_PARTICLES))
    
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    base_pos = np.stack([x, y, z], axis=1).astype(np.float32)
    
    # Initialize field state (near zero)
    field_state = np.random.normal(0, 0.1, (NUM_PARTICLES, 3)).astype(np.float32)
    field_vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    
    # Stars
    num_stars = 12000
    star_pos = np.random.uniform(-2000, 2000, (num_stars, 3))
    star_mag = np.random.uniform(0.5, 2.5, num_stars)
    stars = (star_pos, star_mag)

def draw():
    global field_state, field_vel
    
    py5.background(0, 5, 15)  # Deep midnight blue
    
    # Camera
    t = py5.frame_count / 100.0
    py5.camera(800 * np.cos(t * 0.2), -400 + 200 * np.sin(t * 0.1), 800 * np.sin(t * 0.2), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke_weight(1)
    for p, m in zip(stars[0], stars[1]):
        alpha = 180 + 75 * np.sin(t + m * 10)
        py5.stroke(220, 240, 255, alpha)
        py5.point(*p)

    # Central Glow (Additive)
    py5.push_matrix()
    py5.no_stroke()
    for r in range(8):
        alpha = 15 - r * 1.5
        py5.fill(100, 180, 255, alpha)
        py5.sphere(100 + r * 80)
    py5.pop_matrix()

    # Physics Transition
    # V(phi) = a*|phi|^2 + b*|phi|^4
    # Symmetric: a > 0, b = 0
    # Broken: a < 0, b > 0
    
    if py5.frame_count < TRANSITION_START:
        a = 0.5
        b = 0.0
        target_v = 0.0
    elif py5.frame_count < TRANSITION_END:
        lerp = (py5.frame_count - TRANSITION_START) / (TRANSITION_END - TRANSITION_START)
        a = 0.5 - 1.5 * lerp  # Goes from 0.5 to -1.0
        b = 0.0 + 0.8 * lerp  # Goes from 0.0 to 0.8
        target_v = np.sqrt(max(0, -a / (2 * b))) if b > 0 else 0
    else:
        a = -1.0
        b = 0.8
        target_v = np.sqrt(-a / (2 * b))
        
    # Potential gradient: dV/dphi = 2a*phi + 4b*|phi|^2*phi
    phi_sq = np.sum(field_state**2, axis=1, keepdims=True)
    grad = 2 * a * field_state + 4 * b * phi_sq * field_state
    
    # Update field
    field_vel -= grad
    field_vel += np.random.normal(0, NOISE_STRENGTH, (NUM_PARTICLES, 3))
    field_vel *= DAMPING
    field_state += field_vel * 0.1
    
    # Rendering
    # Actual position = base_pos + field_state * scaling
    render_pos = base_pos + field_state * FIELD_SCALE
    
    # Colors based on field magnitude
    mag = np.sqrt(phi_sq.flatten())
    norm_mag = mag / (target_v + 0.1) if target_v > 0 else mag * 4.0
    
    # Use 10 color bands for smoother transition
    bands = 10
    for i in range(bands):
        mask = (norm_mag >= i / bands) & (norm_mag < (i + 1) / bands)
        if not np.any(mask): continue
        
        # Spectral Palette: White -> Violet -> Cyan -> Indigo -> Gold
        if i < 1: 
            py5.stroke_weight(2.0)
            py5.stroke(255, 255, 255, 255)   # White core
        elif i < 3: 
            py5.stroke_weight(1.5)
            py5.stroke(220, 150, 255, 180) # Violet
        elif i < 6: 
            py5.stroke_weight(1.2)
            py5.stroke(0, 230, 255, 150)   # Cyan
        elif i < 8: 
            py5.stroke_weight(1.0)
            py5.stroke(50, 100, 255, 120)    # Indigo
        else: 
            py5.stroke_weight(1.5)
            py5.stroke(255, 215, 0, 140)         # Gold
        
        pts = render_pos[mask]
        py5.points(pts)

    # Post-process frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264", "-crf", "30", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
