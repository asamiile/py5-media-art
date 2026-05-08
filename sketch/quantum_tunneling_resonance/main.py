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
NUM_PARTICLES = 160_000
NUM_STARS = 12_000

# State
particles = None
p_velocities = None
p_phases = None
stars = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, p_velocities, p_phases, stars
    
    # Initialize particles in a wave packet volume
    # Moving from Z = -800 to +800
    z = np.random.uniform(-1000, -600, NUM_PARTICLES)
    x = np.random.normal(0, 150, NUM_PARTICLES)
    y = np.random.normal(0, 150, NUM_PARTICLES)
    particles = np.stack([x, y, z], axis=-1).astype(np.float32)
    
    # Velocities: mostly Z-forward
    p_velocities = np.zeros_like(particles)
    p_velocities[:, 2] = np.random.uniform(10, 15, NUM_PARTICLES)
    
    # Initial phases
    p_phases = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    
    # Background stars
    stars = np.random.uniform(-1500, 1500, (NUM_STARS, 3)).astype(np.float32)

def draw():
    global particles, p_velocities
    if py5.frame_count % 50 == 0:
        print(f"Frame: {py5.frame_count}/{TOTAL_FRAMES}")
    
    t = py5.frame_count * 0.03
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    py5.camera(600 * np.sin(t * 0.1), 300 * np.cos(t * 0.1), 800 * np.cos(t * 0.1),
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(255, 120)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Barrier Visualization (z=0)
    py5.push_matrix()
    py5.no_fill()
    py5.stroke(200, 50)
    py5.stroke_weight(0.5)
    # A shimmering grid at z=0
    for grid_x in range(-600, 601, 100):
        py5.line(grid_x, -400, 0, grid_x, 400, 0)
    for grid_y in range(-400, 401, 100):
        py5.line(-600, grid_y, 0, 600, grid_y, 0)
    py5.pop_matrix()
    
    # Physics: Quantum Tunneling Resonance
    # Barrier at z=0 to z=40
    barrier_start = 0
    barrier_end = 40
    
    # Update particles
    particles += p_velocities
    
    # Reflection / Tunneling logic
    # When hitting the barrier (z >= barrier_start)
    hit_mask = (particles[:, 2] >= barrier_start) & (particles[:, 2] < barrier_end)
    if np.any(hit_mask):
        # Probability of tunneling (small)
        # e^(-2 * kappa * a)
        tunnel_prob = 0.05
        dice = np.random.rand(np.sum(hit_mask))
        tunnel_mask = dice < tunnel_prob
        reflect_mask = ~tunnel_mask
        
        # Reflect
        # Indices of particles that hit and reflect
        reflect_indices = np.where(hit_mask)[0][reflect_mask]
        p_velocities[reflect_indices, 2] *= -0.8 # Bounce back with some loss
        # Add some jitter to interference
        p_velocities[reflect_indices, 0] += np.random.normal(0, 1.0, len(reflect_indices))
        p_velocities[reflect_indices, 1] += np.random.normal(0, 1.0, len(reflect_indices))
        
        # Tunnel: Just let them pass through the barrier
        # tunnel_indices = np.where(hit_mask)[0][tunnel_mask]
        # p_velocities[tunnel_indices, 2] *= 1.5 # Accelerate? No, just keep going.
    
    # Past the barrier
    past_mask = particles[:, 2] >= barrier_end
    if np.any(past_mask):
        p_velocities[past_mask, 2] += 0.2 # Accelerate after tunneling (energy conservation proxy)
        
    # Recycle particles that go too far or bounce back too far
    recycle_mask = (particles[:, 2] > 1000) | (particles[:, 2] < -1200)
    if np.any(recycle_mask):
        count = np.sum(recycle_mask)
        particles[recycle_mask] = np.stack([
            np.random.normal(0, 150, count),
            np.random.normal(0, 150, count),
            np.random.uniform(-1100, -800, count)
        ], axis=-1)
        p_velocities[recycle_mask] = [0, 0, np.random.uniform(10, 15)]
        
    # Additive Rendering
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Render particles in groups
    # Incident (z < 0, v > 0): Cyan/Violet
    # Reflected (z < 0, v < 0): Deep Violet
    # Tunneling/Past (z > 40): White/Gold
    
    # 1. Incident/Reflected
    ir_mask = particles[:, 2] < barrier_start
    if np.any(ir_mask):
        v_z = p_velocities[ir_mask, 2]
        # Color based on velocity sign and position (interference proxy)
        # We can use a sin wave for interference bands
        z_pos = particles[ir_mask, 2]
        interf = np.sin(z_pos * 0.1 + t * 5)
        
        # Base Hue: 270 (Violet) to 190 (Cyan)
        h = np.where(v_z > 0, 190 + 20 * interf, 270 + 20 * interf)
        s = 70 + 20 * interf
        b = 50 + 40 * np.abs(interf)
        alpha = 30 + 30 * np.abs(interf)
        
        # Binning for speed
        for hue_bin in [190, 210, 270, 290]:
            bin_mask = (h >= hue_bin - 10) & (h < hue_bin + 10)
            if np.any(bin_mask):
                idx = np.where(bin_mask)[0]
                py5.stroke(hue_bin, s[idx].mean(), b[idx].mean(), alpha[idx].mean())
                py5.stroke_weight(1.0)
                py5.points(particles[ir_mask][bin_mask])

    # 2. Tunneling (Past z=40)
    t_mask = particles[:, 2] >= barrier_end
    if np.any(t_mask):
        py5.stroke(45, 80, 100, 60) # Gold
        py5.stroke_weight(2.0)
        py5.points(particles[t_mask])
        # Add a white core
        py5.stroke(0, 0, 100, 40) # White
        py5.stroke_weight(1.0)
        py5.points(particles[t_mask])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run([
            "cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        ], check=True)

if __name__ == "__main__":
    py5.run_sketch()
