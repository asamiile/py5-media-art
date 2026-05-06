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

# Simulation Parameters
NUM_PARTICLES = 150000
NOISE_SCALE = 0.002
CURL_STEP = 1.0

class SynapticParticles:
    def __init__(self, num):
        self.pos = np.random.uniform(-1000, 1000, (num, 3)).astype(np.float32)
        self.vel = np.zeros((num, 3), dtype=np.float32)
        self.hue = np.random.uniform(140, 220, num) # Cyan to Purple
        self.age = np.random.uniform(0, 100, num)

    def update(self, frame_count):
        # Curl Noise calculation (using simple finite difference on Simplex/Perlin)
        # For performance in pure python py5, we'll use a simplified version
        # or just direct noise-based velocity if NumPy noise isn't available.
        # Here we'll use py5.noise via vectorize or loop.
        
        # Simplified Vector Field for large particle count
        # In P3D, we'll use noise to influence velocity directly
        
        # We'll use a small trick: calculate noise at pos
        # Since py5.noise is slow for 150k calls, we'll use a smaller set of nodes
        # and interpolate, or just use a subset per frame.
        
        # Actually, let's use a lower particle count for fluid movement or optimize.
        # Let's try 50k for better frame rates during development.
        pass

def get_curl_noise(x, y, z, scale, time):
    eps = 0.1
    # Finite difference approximation of curl
    # curl F = (dFz/dy - dFy/dz, dFx/dz - dFz/dx, dFy/dx - dFx/dy)
    # Where F is a potential field (scalar noise)
    
    n_x = py5.noise(x * scale, y * scale, z * scale + time)
    n_y = py5.noise(x * scale + 100, y * scale + 100, z * scale + time)
    n_z = py5.noise(x * scale + 200, y * scale + 200, z * scale + time)
    
    return n_x, n_y, n_z # Simplified "noise flow"

particles_pos = None
particles_vel = None
particles_hue = None
nodes = None

def setup():
    global particles_pos, particles_vel, particles_hue, nodes
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 255)
    py5.background(10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    num = 80000
    particles_pos = np.random.uniform(-800, 800, (num, 3)).astype(np.float32)
    particles_vel = np.zeros((num, 3), dtype=np.float32)
    particles_hue = np.random.uniform(130, 200, num).astype(np.float32) # Cyan/Blue/Violet
    
    # Synaptic attractor nodes
    nodes = np.random.uniform(-600, 600, (30, 3)).astype(np.float32)

def draw():
    global particles_pos, particles_vel, particles_hue, nodes
    
    # Semi-transparent background for trails (simulated in P3D by not clearing fully or using PGraphics)
    # P3D doesn't support alpha-background well, so we'll use additive points with low alpha
    py5.background(5, 5, 20) 
    
    # Camera
    cam_r = 1200
    cam_x = cam_r * py5.cos(py5.frame_count * 0.005)
    cam_z = cam_r * py5.sin(py5.frame_count * 0.005)
    py5.camera(cam_x, -200, cam_z, 0, 0, 0, 0, 1, 0)
    
    # Update a subset of particles for performance
    # or just use numpy operations for the whole set if we keep it simple.
    
    # Noise influence
    t = py5.frame_count * 0.01
    # Simple drift
    particles_pos[:, 0] += np.sin(particles_pos[:, 1] * 0.005 + t) * 0.5
    particles_pos[:, 1] += np.cos(particles_pos[:, 2] * 0.005 + t) * 0.5
    particles_pos[:, 2] += np.sin(particles_pos[:, 0] * 0.005 + t) * 0.5
    
    # Node attraction
    # For a subset of nodes to keep it fast
    target_node = nodes[py5.frame_count % len(nodes)]
    dir_to_node = target_node - particles_pos
    dist = np.linalg.norm(dir_to_node, axis=1, keepdims=True)
    particles_vel += (dir_to_node / (dist + 100)) * 0.05
    
    particles_pos += particles_vel
    particles_vel *= 0.98 # Damping
    
    # Reset particles that go too far
    mask = np.linalg.norm(particles_pos, axis=1) > 1200
    particles_pos[mask] = np.random.uniform(-800, 800, (np.sum(mask), 3))
    particles_vel[mask] = 0
    
    # Draw
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # We'll use multiple hue bands for variety
    num_bins = 6
    for h_bin in range(num_bins):
        h = 130 + (h_bin * 15)
        mask = (particles_hue >= h) & (particles_hue < h + 15)
        if np.any(mask):
            # Pulse brightness and alpha
            s = py5.sin(t * 2 + h_bin)
            b = 180 + 75 * s
            alpha = 180 + 75 * s
            py5.stroke(h, 200, b, alpha)
            py5.stroke_weight(1.5) # Increased weight
            py5.points(particles_pos[mask])
    
    # Draw Synaptic Nodes with "Neural Flares"
    for node in nodes:
        # Distance to camera for scaling glow
        d_cam = np.linalg.norm(node - np.array([cam_x, -200, cam_z]))
        # Manual map: 500 -> 40, 2000 -> 10
        t_map = np.clip((d_cam - 500) / (2000 - 500), 0, 1)
        flare_size = 40 + (10 - 40) * t_map
        
        # Central node
        py5.stroke_weight(6)
        py5.stroke(220, 150, 255, 200)
        py5.point(*node)
        
        # Pulsing corona
        py5.push_matrix()
        py5.translate(*node)
        py5.no_stroke()
        for i in range(3):
            alpha = 40 - i * 10
            py5.fill(220, 150, 255, alpha)
            py5.sphere(flare_size + i * 15 * (1 + 0.5 * py5.sin(t * 8)))
        py5.pop_matrix()
        
    py5.hint(py5.ENABLE_DEPTH_TEST)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        mid = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
