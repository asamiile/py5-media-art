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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 100000
NUM_PLUMES = 16
GRAVITY = 0.25
VISCOSITY = 0.94
TURBULENCE = 0.2

# State
pos = None
vel = None
p_type = None  # 0 for light, 1 for heavy
plume_pos = None
plume_strength = None

def setup():
    global pos, vel, p_type, plume_pos, plume_strength
    py5.size(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles
    # Light fluid on bottom (z < 0), Heavy fluid on top (z > 0)
    pos = np.random.uniform(-400, 400, (NUM_PARTICLES, 3))
    # Add a bit of interfacial noise
    pos[:, 2] = np.random.normal(0, 50, NUM_PARTICLES)
    
    vel = np.zeros((NUM_PARTICLES, 3))
    
    # Type based on initial position (0: light/rising, 1: heavy/sinking)
    p_type = (pos[:, 2] > 0).astype(int)
    
    # Initialize plume centers at the interface z=0
    plume_pos = np.random.uniform(-400, 400, (NUM_PLUMES, 3))
    plume_pos[:, 2] = 0
    # Alternating sinking/rising
    plume_strength = np.random.uniform(2.0, 5.0, NUM_PLUMES)
    plume_strength[::2] *= -1 # Rising plumes
    
def draw():
    global pos, vel, plume_pos
    
    t = py5.frame_count / FPS
    
    # 1. Physics Update
    # Update plume positions slightly (drifting interface)
    plume_pos[:, 0] += np.sin(t * 0.5 + plume_strength) * 0.5
    plume_pos[:, 1] += np.cos(t * 0.7 - plume_strength) * 0.5
    
    # Calculate forces
    # Plume advection (optimized loop)
    plume_force = np.zeros_like(pos)
    for i in range(NUM_PLUMES):
        d = pos - plume_pos[i]
        d2 = np.sum(d**2, axis=1, keepdims=True) + 800.0
        plume_force += (plume_strength[i] / d2) * d
    
    # Limit force range
    plume_force = np.clip(plume_force, -1.5, 1.5)
    
    # Buoyancy Force
    # Heavy (type 1) falls, Light (type 0) rises
    buoyancy = np.zeros_like(pos)
    buoyancy[:, 2] = np.where(p_type == 1, -GRAVITY, GRAVITY)
    
    # Turbulence (noise)
    noise = np.random.normal(0, TURBULENCE, (NUM_PARTICLES, 3))
    
    # Update Velocity
    vel = vel * VISCOSITY + plume_force * 0.1 + buoyancy + noise
    pos += vel
    
    # Wrap XY, Clamp Z
    pos[:, :2] = (pos[:, :2] + 600) % 1200 - 600
    # If a particle goes too far, recycle it near the interface
    reset_mask = np.abs(pos[:, 2]) > 600
    if np.any(reset_mask):
        pos[reset_mask, 2] = np.random.normal(0, 10, np.sum(reset_mask))
        vel[reset_mask] = 0
    
    # 2. Rendering
    py5.background(0)
    
    py5.blend_mode(py5.ADD)
    
    # Manual Projection
    # move back, rotate
    cx, sx = np.cos(1.1 + np.sin(t * 0.2) * 0.1), np.sin(1.1 + np.sin(t * 0.2) * 0.1)
    rz = t * 0.1
    cz, sz = np.cos(rz), np.sin(rz)
    
    # Rotate Z
    px = pos[:, 0] * cz - pos[:, 1] * sz
    py = pos[:, 0] * sz + pos[:, 1] * cz
    pz = pos[:, 2]
    
    # Rotate X (oblique)
    py_final = py * cx - pz * sx
    pz_final = py * sx + pz * cx
    
    # Translate and Project
    z_final = pz_final - 400
    f = 1400 / (np.abs(z_final) + 1e-6)
    screen_x = px * f + py5.width/2
    screen_y = py_final * f + py5.height/2
    
    # Color by type and velocity
    v_mag = np.sqrt(np.sum(vel**2, axis=1))
    # Heavy: Orange/Red (10-40)
    # Light: Blue/Azure (180-240)
    h_vals = np.where(p_type == 1, 
                      20 + 25 * np.clip(v_mag/3, 0, 1), 
                      200 + 40 * np.clip(v_mag/3, 0, 1))
    
    # Batch points by hue
    num_buckets = 6
    for i in range(num_buckets):
        h_min = 20 + i * (220/num_buckets)
        h_max = h_min + (220/num_buckets)
        mask = (h_vals >= h_min) & (h_vals < h_max)
        if not np.any(mask): continue
        
        py5.stroke(h_min % 360, 85, 100, 35)
        py5.stroke_weight(2.6)
        py5.points(np.stack([screen_x[mask], screen_y[mask]], axis=1))
    
    # 3. Save/Exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), 
                        str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
