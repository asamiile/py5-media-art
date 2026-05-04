from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Physics Constants
DAMPING = 0.98
SPRING_STRENGTH = 0.1
ITERATIONS = 5

class Particle:
    def __init__(self, x, y, pinned=False):
        self.pos = np.array([float(x), float(y)])
        self.old_pos = self.pos.copy()
        self.acc = np.zeros(2)
        self.pinned = pinned
        self.radius = 2

    def update(self):
        if self.pinned: return
        vel = (self.pos - self.old_pos) * DAMPING
        self.old_pos = self.pos.copy()
        self.pos += vel + self.acc
        self.acc[:] = 0

    def apply_force(self, force):
        self.acc += force

class Spring:
    def __init__(self, p1, p2, strength=SPRING_STRENGTH):
        self.p1 = p1
        self.p2 = p2
        self.rest_len = np.linalg.norm(p1.pos - p2.pos)
        self.strength = strength

    def constrain(self):
        delta = self.p2.pos - self.p1.pos
        dist = np.linalg.norm(delta)
        if dist < 1e-6: return
        diff = (dist - self.rest_len) / dist
        offset = delta * diff * self.strength * 0.5
        if not self.p1.pinned: self.p1.pos += offset
        if not self.p2.pinned: self.p2.pos -= offset

particles = []
springs = []

def setup():
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create Radial Lattice
    center = np.array([py5.width/2, py5.height/2])
    num_rings = 8
    pts_per_ring = 24
    
    ring_particles = []
    
    for r in range(num_rings):
        radius = 50 + r * 45
        current_ring = []
        for i in range(pts_per_ring):
            angle = (i / pts_per_ring) * np.pi * 2
            x = center[0] + np.cos(angle) * radius
            y = center[1] + np.sin(angle) * radius
            p = Particle(x, y, pinned=(r == num_rings - 1)) # Pin outer ring
            particles.append(p)
            current_ring.append(p)
        ring_particles.append(current_ring)
        
    # Connect Springs
    for r in range(num_rings):
        for i in range(pts_per_ring):
            p = ring_particles[r][i]
            # Neighbors in ring
            p_next = ring_particles[r][(i + 1) % pts_per_ring]
            springs.append(Spring(p, p_next))
            # Neighbors in next ring
            if r < num_rings - 1:
                p_out = ring_particles[r+1][i]
                springs.append(Spring(p, p_out))
                # Diagonals for stability
                p_out_next = ring_particles[r+1][(i + 1) % pts_per_ring]
                springs.append(Spring(p, p_out_next, strength=0.05))

def draw():
    py5.background(240, 80, 5, 100) # Very dark indigo background
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Central metabolic pulse
    center = np.array([py5.width/2, py5.height/2])
    pulse_mag = 4.0 + 2.0 * np.sin(t * np.pi * 8)
    for p in particles:
        if not p.pinned:
            dist = np.linalg.norm(p.pos - center)
            force_dir = (p.pos - center) / (dist + 1)
            # Wave propagation
            wave = np.sin(dist * 0.08 - t * np.pi * 12)
            p.apply_force(force_dir * wave * pulse_mag * 0.5)
            
    # Physics update
    for p in particles: p.update()
    for _ in range(ITERATIONS):
        for s in springs: s.constrain()
        
    # Rendering
    # Glow Pass
    for s in springs:
        dist = np.linalg.norm(s.p1.pos - s.p2.pos)
        stress = abs(dist - s.rest_len)
        
        hue = (200 + stress * 30 + np.sin(t * np.pi * 2) * 40) % 360
        sat = 50 + stress * 50
        bri = 60 + stress * 40
        
        # Glow (thick, faint)
        py5.stroke_weight(4.0)
        py5.stroke(hue, sat, bri, 10 + stress * 10)
        py5.line(s.p1.pos[0], s.p1.pos[1], s.p2.pos[0], s.p2.pos[1])
        
        # Core line (thin, bright)
        py5.stroke_weight(1.5)
        py5.stroke(hue, sat, bri, 60 + stress * 40)
        py5.line(s.p1.pos[0], s.p1.pos[1], s.p2.pos[0], s.p2.pos[1])
        
    # Draw Nodes (Core)
    py5.no_stroke()
    for p in particles:
        dist = np.linalg.norm(p.pos - center)
        if dist < 120:
            core_pulse = np.sin(t * np.pi * 15 - dist * 0.1)
            py5.fill(280, 80, 100, 15 + core_pulse * 10)
            py5.circle(p.pos[0], p.pos[1], 6 + core_pulse * 4)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Preview
    if py5.frame_count == 1:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Update preview to a middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
