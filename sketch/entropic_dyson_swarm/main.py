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
NUM_PARTICLES = 120000
G = 1.5
STAR_MASS = 1000
SWARM_RADIUS = 350
JITTER = 0.05
NOISE_SCALE = 0.005

class DysonSwarm:
    def __init__(self, num_particles):
        self.num_particles = num_particles
        
        # Positions: Initialized in a shell with thickness
        theta = np.random.uniform(0, 2 * np.pi, num_particles)
        phi = np.arccos(np.random.uniform(-1, 1, num_particles))
        r = SWARM_RADIUS + np.random.normal(0, 20, num_particles)
        
        self.pos = np.zeros((num_particles, 3), dtype=np.float32)
        self.pos[:, 0] = r * np.sin(phi) * np.cos(theta)
        self.pos[:, 1] = r * np.sin(phi) * np.sin(theta)
        self.pos[:, 2] = r * np.cos(phi)
        
        # Velocities: Keplerian (perpendicular to radius)
        # v = sqrt(G * M / r)
        v_mag = np.sqrt(G * STAR_MASS / r)
        
        # Tangent vector (orthogonal to pos)
        tangent = np.zeros_like(self.pos)
        tangent[:, 0] = -self.pos[:, 1]
        tangent[:, 1] = self.pos[:, 0]
        # Normalize tangent
        norms = np.linalg.norm(tangent, axis=1, keepdims=True)
        tangent /= (norms + 1e-6)
        
        self.vel = tangent * v_mag[:, np.newaxis]
        # Add some random inclination and noise
        self.vel += np.random.normal(0, 0.2, (num_particles, 3))

    def update(self, frame_count):
        # Gravitational attraction
        r_vec = -self.pos
        r_mag = np.linalg.norm(r_vec, axis=1, keepdims=True)
        r_hat = r_vec / (r_mag + 1e-6)
        
        acc = G * STAR_MASS / (r_mag**2 + 100) * r_hat
        
        # Entropic perturbation (noise field)
        # Using frame_count to animate the noise
        noise_input = self.pos * NOISE_SCALE
        # Simplified noise for performance (using sin/cos based on pos)
        perturb = np.zeros_like(self.pos)
        perturb[:, 0] = np.sin(noise_input[:, 1] + frame_count * 0.02)
        perturb[:, 1] = np.cos(noise_input[:, 2] + frame_count * 0.02)
        perturb[:, 2] = np.sin(noise_input[:, 0] + frame_count * 0.02)
        
        acc += perturb * 0.05
        
        # Integration
        self.vel += acc
        self.pos += self.vel
        
        # Damping to maintain stability
        self.vel *= 0.999

swarm = None
starfield = None

def setup():
    global swarm, starfield
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    swarm = DysonSwarm(NUM_PARTICLES)
    
    # Pre-generate starfield
    starfield = np.random.uniform(-2000, 2000, (2000, 3))

def draw():
    global swarm, starfield
    py5.background(5, 5, 15) # Deep indigo
    
    # Camera setup
    py5.perspective(py5.PI/3, py5.width/py5.height, 1, 10000)
    cam_r = 1200
    cam_x = cam_r * np.cos(py5.frame_count * 0.005)
    cam_z = cam_r * np.sin(py5.frame_count * 0.005)
    py5.camera(cam_x, -400, cam_z, 0, 0, 0, 0, 1, 0)
    
    # Draw starfield
    py5.stroke(200, 200, 255, 150)
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    for s in starfield:
        py5.vertex(*s)
    py5.end_shape()
    
    # Update simulation
    swarm.update(py5.frame_count)
    
    # Draw central star (with glow)
    py5.push_matrix()
    py5.no_stroke()
    # Inner core
    py5.fill(255, 255, 220)
    py5.sphere(60)
    # Corona layers
    py5.hint(py5.DISABLE_DEPTH_TEST)
    for i in range(5):
        alpha = 50 - i * 8
        py5.fill(255, 200, 100, alpha)
        py5.sphere(65 + i * 15)
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.pop_matrix()
    
    # Draw Dyson swarm particles
    py5.hint(py5.DISABLE_DEPTH_TEST) # Additive feel
    py5.begin_shape(py5.POINTS)
    
    # Calculate colors based on distance and velocity
    speeds = np.linalg.norm(swarm.vel, axis=1)
    max_speed = np.max(speeds)
    
    # Sub-sample for drawing if needed, but 120k is okay for P3D POINTS
    for i in range(swarm.num_particles):
        s = speeds[i] / max_speed
        # Blend between Cyan and Gold
        r = py5.lerp(0, 255, s)
        g = py5.lerp(200, 215, s)
        b = py5.lerp(255, 0, s)
        py5.stroke(r, g, b, 180)
        py5.vertex(swarm.pos[i, 0], swarm.pos[i, 1], swarm.pos[i, 2])
    py5.end_shape()
    
    # Draw Energy Beams (subset)
    py5.stroke(255, 255, 255, 20)
    py5.stroke_weight(0.5)
    for i in range(0, swarm.num_particles, 1000):
        py5.line(swarm.pos[i, 0], swarm.pos[i, 1], swarm.pos[i, 2], 0, 0, 0)
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
