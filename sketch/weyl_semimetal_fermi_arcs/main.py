from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 120000
NODE_DIST = 200
WEYL_NODES = np.array([[-NODE_DIST, 0, 0], [NODE_DIST, 0, 0]], dtype=np.float32)

class WeylSimulation:
    def __init__(self, n_particles):
        self.n = n_particles
        self.pos = np.zeros((n_particles, 3), dtype=np.float32)
        self.vel = np.zeros((n_particles, 3), dtype=np.float32)
        self.phase = np.random.rand(n_particles).astype(np.float32) * np.pi * 2
        self.freq = np.random.uniform(0.5, 1.5, n_particles).astype(np.float32)
        self.offset = np.random.rand(n_particles).astype(np.float32) * 1.0
        self.type = np.random.randint(0, 2, n_particles) # 0: Fermi Arcs, 1: Chiral Bulk
        self.reset_all()

    def reset_all(self):
        # Fermi Arcs
        mask_arc = self.type == 0
        n_arc = np.sum(mask_arc)
        theta = np.random.uniform(0, np.pi, n_arc).astype(np.float32)
        phi = np.random.uniform(-np.pi/2, np.pi/2, n_arc).astype(np.float32)
        # Semicircular arcs connecting -NODE_DIST to NODE_DIST
        r = NODE_DIST
        self.pos[mask_arc, 0] = r * np.cos(theta)
        self.pos[mask_arc, 1] = r * np.sin(theta) * np.cos(phi)
        self.pos[mask_arc, 2] = r * np.sin(theta) * np.sin(phi)
        
        # Chiral Bulk (particles moving between nodes)
        mask_bulk = self.type == 1
        n_bulk = np.sum(mask_bulk)
        self.pos[mask_bulk, 0] = np.random.uniform(-NODE_DIST, NODE_DIST, n_bulk)
        self.pos[mask_bulk, 1] = np.random.normal(0, 10, n_bulk)
        self.pos[mask_bulk, 2] = np.random.normal(0, 10, n_bulk)

    def update(self, t):
        # Update Fermi Arcs (breathing motion)
        mask_arc = self.type == 0
        angle = t * self.freq[mask_arc] * 0.2 + self.phase[mask_arc]
        # Oscillate the radius and shape
        amp = 1.0 + 0.1 * np.sin(t * 0.5 + self.phase[mask_arc])
        r = NODE_DIST
        
        # We want arcs to stay pinned at nodes: x = +/- NODE_DIST
        # Simple parametric arc: x = NODE_DIST * cos(theta), y = R * sin(theta)
        # theta from 0 to pi
        theta = np.linspace(0, np.pi, np.sum(mask_arc), dtype=np.float32)
        # Shuffle theta for randomness if needed, but here they are fixed to their "slot"
        # Let's use the initial theta/phi we stored
        # Actually, let's just re-calculate based on t
        
        # Better: keep initial theta/phi and just oscillate
        pass

    def get_points(self, t):
        # Fermi Arcs: semi-ellipses in 3D
        mask_arc = self.type == 0
        n_arc = np.sum(mask_arc)
        
        # Each particle is assigned a theta (arc position) and a phi (arc plane)
        # and a phase for breathing
        u = (self.phase[mask_arc] / (2*np.pi) + t * 0.01 * self.freq[mask_arc]) % 1.0
        theta = u * np.pi # 0 to pi
        
        # Plane angle
        phi = self.phase[mask_arc] * 2.0 
        
        # Radius of the arc sphere
        r = NODE_DIST
        # Breath
        r_mod = r * (1.0 + 0.05 * np.sin(t * 0.1 + self.phase[mask_arc] * 10))
        
        x = r_mod * np.cos(theta)
        y = r_mod * np.sin(theta) * np.cos(phi)
        z = r_mod * np.sin(theta) * np.sin(phi)
        
        self.pos[mask_arc, 0] = x
        self.pos[mask_arc, 1] = y
        self.pos[mask_arc, 2] = z
        
        # Chiral Bulk: linear flow with turbulence
        mask_bulk = self.type == 1
        self.pos[mask_bulk, 0] = ((self.pos[mask_bulk, 0] + NODE_DIST + 2) % (2 * NODE_DIST)) - NODE_DIST
        # Add some spiral/twist
        self.pos[mask_bulk, 1] = 15 * np.sin(self.pos[mask_bulk, 0] * 0.02 + t * 0.1 + self.phase[mask_bulk])
        self.pos[mask_bulk, 2] = 15 * np.cos(self.pos[mask_bulk, 0] * 0.02 + t * 0.1 + self.phase[mask_bulk])

        return self.pos

sim = WeylSimulation(NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 15)

def draw():
    t = py5.frame_count
    
    # Render logic
    py5.background(5, 5, 15)
    
    # 3D Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.005)
    py5.rotate_x(np.sin(t * 0.003) * 0.2)
    
    # Draw Weyl Nodes
    py5.no_stroke()
    for node_pos in WEYL_NODES:
        py5.push_matrix()
        py5.translate(*node_pos)
        # Pulsing glow
        glow_size = 15 + 5 * np.sin(t * 0.1)
        py5.fill(255, 255, 255, 150)
        py5.sphere(glow_size)
        py5.fill(0, 200, 255, 50)
        py5.sphere(glow_size * 2)
        py5.pop_matrix()

    # Draw Particles
    points = sim.get_points(t)
    
    # We'll use py5.points() for speed
    # But we want different colors for Arcs and Bulk
    
    # Arcs: Cyan/Magenta
    mask_arc = sim.type == 0
    arc_points = points[mask_arc]
    
    py5.stroke_weight(1.5)
    # Spectral shift based on x position
    # From -NODE_DIST to NODE_DIST: Cyan to Magenta
    norm_x = (arc_points[:, 0] + NODE_DIST) / (2 * NODE_DIST)
    
    # Manual loop or multi-point? 
    # To be fast, let's use a vertex array approach if possible, 
    # but py5.points() is easiest. 
    # Let's split into chunks for color
    for i in range(10):
        low = i / 10.0
        high = (i + 1) / 10.0
        m = (norm_x >= low) & (norm_x < high)
        if np.any(m):
            # Interp color Cyan (180) to Magenta (300)
            hue = 180 + 120 * (i / 10.0)
            py5.color_mode(py5.HSB, 360, 100, 100, 100)
            py5.stroke(hue, 80, 100, 40)
            py5.points(arc_points[m])
            py5.color_mode(py5.RGB, 255, 255, 255, 255)

    # Bulk: White/Electric
    mask_bulk = sim.type == 1
    bulk_points = points[mask_bulk]
    py5.stroke(255, 255, 255, 60)
    py5.stroke_weight(1.0)
    py5.points(bulk_points)
    
    py5.pop_matrix()

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure ffmpeg is called correctly
        # Note: the workflow says generate output.mp4 and commit it
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "17",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        # Save preview from middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
