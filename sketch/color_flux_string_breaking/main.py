import numpy as np
from pathlib import Path
import subprocess
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation parameters
MAX_PARTICLES = 30000
particles = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)  # x, y, z
velocities = np.zeros((MAX_PARTICLES, 3), dtype=np.float32)
charges = np.zeros(MAX_PARTICLES, dtype=np.int8)  # 0: Red, 1: Green, 2: Blue, 3: Anti-Red, etc.
active = np.zeros(MAX_PARTICLES, dtype=bool)

# Initial particles
num_active = 600
center = np.array([SIZE[0]/2, SIZE[1]/2, 0])
particles[:num_active] = center + np.random.normal(0, 100, (num_active, 3))
velocities[:num_active] = np.random.normal(0, 2, (num_active, 3))
charges[:num_active] = np.random.randint(0, 6, num_active)
active[:num_active] = True

# Additive colors for Red, Green, Blue, Anti-R (Cyan), Anti-G (Magenta), Anti-B (Yellow)
colors = [
    (255, 0, 0),     # R
    (0, 255, 0),     # G
    (0, 0, 255),     # B
    (0, 255, 255),   # Anti-R
    (255, 0, 255),   # Anti-G
    (255, 255, 0)    # Anti-B
]

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    py5.background(0)
    py5.blend_mode(py5.ADD)

def draw():
    global num_active, particles, velocities, charges, active
    
    # Very slight fade for persistence
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 12)
    py5.rect(0, 0, py5.width, py5.height)
    py5.blend_mode(py5.ADD)
    
    if num_active == 0:
        return
        
    p_active = particles[:num_active]
    v_active = velocities[:num_active]
    c_active = charges[:num_active]
    
    # String tension force (Confinement)
    # Towards center
    dir_center = center - p_active
    dist_center = np.linalg.norm(dir_center, axis=1, keepdims=True) + 1e-5
    force_center = (dir_center / dist_center) * 0.05
    
    # Adding a chaotic expansion force
    v_active += force_center
    
    # Magnetic/chiral twist based on charge
    twist = np.zeros_like(v_active)
    twist[:, 0] = -v_active[:, 1]
    twist[:, 1] = v_active[:, 0]
    
    charge_signs = np.where(c_active < 3, 1.0, -1.0)[:, None]
    v_active += twist * 0.05 * charge_signs
    
    # Update positions
    p_active += v_active
    
    # Rendering and 'String Breaking' logic
    # Find particles that are too far from center and "snap" them
    snap_threshold = 400.0
    snapped = dist_center.flatten() > snap_threshold
    
    num_snapped = np.sum(snapped)
    if num_snapped > 0 and num_active + num_snapped * 2 < MAX_PARTICLES:
        # String breaking: creating new particle-antiparticle pairs
        new_indices = np.arange(num_active, num_active + num_snapped * 2)
        parent_indices = np.where(snapped)[0]
        
        # New particles spawn near the snap point
        spawn_pos = p_active[parent_indices]
        
        # Two new particles per snap
        particles[new_indices[0::2]] = spawn_pos + np.random.normal(0, 5, (num_snapped, 3))
        particles[new_indices[1::2]] = spawn_pos + np.random.normal(0, 5, (num_snapped, 3))
        
        # Opposite high velocities
        new_v = np.random.normal(0, 8, (num_snapped, 3))
        velocities[new_indices[0::2]] = new_v
        velocities[new_indices[1::2]] = -new_v
        
        # Random color/anticolor
        new_c = np.random.randint(0, 3, num_snapped)
        charges[new_indices[0::2]] = new_c
        charges[new_indices[1::2]] = new_c + 3
        
        active[new_indices] = True
        
        # Pull the snapped parents back towards center violently (tension release)
        v_active[parent_indices] = dir_center[parent_indices] * 0.02
        
        # Draw blinding white flashes at snap points
        py5.stroke(255, 255, 255, 200)
        py5.stroke_weight(4)
        py5.begin_shape(py5.POINTS)
        for i in range(num_snapped):
            pos = spawn_pos[i]
            py5.vertex(pos[0], pos[1], pos[2])
        py5.end_shape()
        
        num_active += num_snapped * 2

    # Draw all active particles
    py5.stroke_weight(1.5)
    
    # Group by charge for faster rendering
    for charge_idx, color in enumerate(colors):
        mask = c_active == charge_idx
        if not np.any(mask):
            continue
            
        group_p = p_active[mask]
        
        py5.stroke(*color, 150)
        py5.begin_shape(py5.POINTS)
        for i in range(len(group_p)):
            py5.vertex(group_p[i, 0], group_p[i, 1], group_p[i, 2])
        py5.end_shape()

    # Damping to prevent infinite velocity explosion
    v_active *= 0.98

    # Camera rotation to see 3D structure
    t = py5.frame_count * 0.01
    py5.camera(center[0] + np.cos(t) * 800, center[1] + np.sin(t) * 800, 800,
               center[0], center[1], 0,
               0, 1, 0)
               
    # Ensure drawing onto background plane when needed
    py5.push_matrix()
    py5.reset_matrix()
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()
