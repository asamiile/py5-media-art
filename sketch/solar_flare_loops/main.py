from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation parameters
NUM_LOOPS = 24
NUM_PARTICLES_PER_LOOP = 2000
NUM_PARTICLES = NUM_LOOPS * NUM_PARTICLES_PER_LOOP

# Loop definitions (anchors and control points)
loops_anchors = np.zeros((NUM_LOOPS, 4, 3)) # 4 points: start, cp1, cp2, end
# Particles [loop_index, parameter_t, speed, offset]
particles_data = np.zeros((NUM_PARTICLES, 4))

def setup():
    global loops_anchors, particles_data
    py5.size(*SIZE, py5.P3D)
    py5.background(2, 2, 8)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize solar surface sphere radius
    R = 250
    
    for i in range(NUM_LOOPS):
        # Start and end points on the sphere surface
        lat1 = np.random.uniform(-np.pi/4, np.pi/4)
        lon1 = np.random.uniform(0, 2 * np.pi)
        lat2 = lat1 + np.random.uniform(-0.5, 0.5)
        lon2 = lon1 + np.random.uniform(0.2, 1.0)
        
        p1 = np.array([R * np.cos(lat1) * np.cos(lon1), R * np.sin(lat1), R * np.cos(lat1) * np.sin(lon1)])
        p4 = np.array([R * np.cos(lat2) * np.cos(lon2), R * np.sin(lat2), R * np.cos(lat2) * np.sin(lon2)])
        
        # Control points pulled outward by "magnetic pressure"
        height = np.random.uniform(100, 400)
        mid = (p1 + p4) / 2.0
        up = mid / np.linalg.norm(mid)
        p2 = p1 + up * height * 0.8
        p3 = p4 + up * height * 0.8
        
        loops_anchors[i] = [p1, p2, p3, p4]
        
    # Initialize particles
    for i in range(NUM_PARTICLES):
        loop_idx = i // NUM_PARTICLES_PER_LOOP
        t = np.random.uniform(0, 1)
        speed = np.random.uniform(0.005, 0.015)
        offset = np.random.uniform(0, 2 * np.pi)
        particles_data[i] = [loop_idx, t, speed, offset]

def draw():
    global particles_data, loops_anchors
    py5.background(0, 0, 2)
    
    t_anim = py5.frame_count / FPS
    
    # Background starfield
    np.random.seed(42)
    for _ in range(300):
        x, y = np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])
        z_star = np.random.uniform(-1000, -200)
        s = np.random.uniform(0.5, 2.5)
        alpha = np.random.uniform(30, 80)
        py5.stroke(0, 0, 100, alpha)
        py5.stroke_weight(s)
        py5.push_matrix()
        py5.translate(x, y, z_star)
        py5.point(0, 0)
        py5.pop_matrix()
    np.random.seed(None)

    # Solar "core" and chromosphere glow
    py5.push_matrix()
    py5.translate(SIZE[0]//2, SIZE[1]//2, 0)
    py5.rotate_y(t_anim * 0.05)
    
    # Layered glow
    for i in range(12):
        r_glow = 245 + i * 3
        alpha = 20 - i * 1.5
        py5.fill(40, 80, 100, alpha)
        py5.no_stroke()
        py5.sphere(r_glow)
    
    # Render Loops and Plasma
    py5.rotate_x(py5.radians(15))
    
    # Vectorized Bezier evaluation
    indices = particles_data[:, 0].astype(int)
    ts = particles_data[:, 1]
    
    # Update ts
    particles_data[:, 1] = (ts + particles_data[:, 2]) % 1.0
    
    P1 = loops_anchors[indices, 0]
    P2 = loops_anchors[indices, 1]
    P3 = loops_anchors[indices, 2]
    P4 = loops_anchors[indices, 3]
    
    # Oscillate control points for "pulsing" magnetic field
    pulse = 1.0 + 0.12 * np.sin(t_anim * 3.0 + indices * 0.7)
    P2 = P2 * pulse[:, np.newaxis]
    P3 = P3 * pulse[:, np.newaxis]
    
    it = 1.0 - ts
    pos = (it**3)[:, np.newaxis] * P1 + \
          (3 * it**2 * ts)[:, np.newaxis] * P2 + \
          (3 * it * ts**2)[:, np.newaxis] * P3 + \
          (ts**3)[:, np.newaxis] * P4
    
    # Add volume/thickness to the loops
    # Per-particle offset based on its parameter t and index
    np.random.seed(42)
    offsets = np.random.normal(0, 4, (NUM_PARTICLES, 3)) * np.sin(ts * np.pi)[:, np.newaxis]
    pos += offsets
    np.random.seed(None)
          
    # Rendering particles
    dist = np.linalg.norm(pos, axis=1)
    # Hue: 45 (Gold) at surface, 15 (Fire Red) at peak
    hues = py5.remap(dist, 250, 650, 45, 15)
    
    # Brightness pulses
    brights = 85 + 15 * np.sin(ts * 15.0 + particles_data[:, 3] + t_anim * 8.0)
    
    # Rendering in batches
    for h_target in range(15, 51, 5):
        mask = (hues >= h_target) & (hues < h_target + 5)
        if np.any(mask):
            # Core layer (white-hot)
            py5.stroke(h_target, 20, 100, 70)
            py5.stroke_weight(1.8)
            py5.points(pos[mask])
            
            # Plasma glow layer
            py5.stroke(h_target, 100, 100, 25)
            py5.stroke_weight(5.0)
            py5.points(pos[mask])
            
    py5.pop_matrix()

    # Save frames and exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
