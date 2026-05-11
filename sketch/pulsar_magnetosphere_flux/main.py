import py5
import numpy as np
import subprocess
from pathlib import Path
import sys

# Add project root to path for lib imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

# Configuration
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 60000
ROTATION_SPEED = 0.08
PRECESSION_SPEED = 0.005
INCLINATION = 0.8  # Increased inclination for better field view
LIGHT_CYLINDER = 600.0
PARTICLE_LIFESPAN = 120
STAR_RADIUS = 25.0

# State
pos = None
vel = None
age = None
m_axis = None

def setup():
    global pos, vel, age
    py5.size(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize particles
    pos = np.zeros((NUM_PARTICLES, 3))
    vel = np.zeros((NUM_PARTICLES, 3))
    age = np.random.randint(0, PARTICLE_LIFESPAN, NUM_PARTICLES)
    
    # Seed initially
    for i in range(NUM_PARTICLES):
        reset_particle(i)
    
    FRAMES_DIR.mkdir(exist_ok=True)

def reset_particle(i):
    # Seed in a volume near the star to avoid over-clumping
    r = STAR_RADIUS * (1.0 + np.random.uniform(0, 5.0))
    phi = np.random.uniform(0, 2 * np.pi)
    theta = np.arccos(np.random.uniform(-1, 1))
    pos[i] = r * np.array([
        np.sin(theta) * np.cos(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(theta)
    ])
    vel[i] = np.zeros(3)
    age[i] = np.random.randint(0, PARTICLE_LIFESPAN)

def get_field(p, m):
    r_mag = np.linalg.norm(p)
    if r_mag < 1.0: return np.zeros(3)
    
    # Dipole field: B = (3(m.r)r - m|r|^2) / |r|^5
    dot = np.dot(m, p)
    B = (3 * dot * p - m * (r_mag**2)) / (r_mag**5)
    
    # Normalize for streamline following
    B_mag = np.linalg.norm(B)
    if B_mag > 0:
        B /= B_mag
    
    # Add toroidal component (twist from rotation)
    # Beyond light cylinder, toroidal dominates
    dist_xy = np.sqrt(p[0]**2 + p[1]**2)
    twist_factor = np.clip(dist_xy / LIGHT_CYLINDER, 0, 2)
    toroidal = np.array([-p[1], p[0], 0]) / (dist_xy + 1e-6)
    
    return B + toroidal * twist_factor * 0.5

def draw():
    global pos, vel, age, m_axis
    t = py5.frame_count
    
    # 1. Update magnetic axis
    # Precession + Rotation
    prec_phi = t * PRECESSION_SPEED
    rot_phi = t * ROTATION_SPEED
    
    # Base inclination
    m_base = np.array([np.sin(INCLINATION), 0, np.cos(INCLINATION)])
    
    # Rotate around z-axis
    m_axis = np.array([
        m_base[0] * np.cos(rot_phi),
        m_base[0] * np.sin(rot_phi),
        m_base[1] if len(m_base) > 2 else m_base[2] # Fixed indexing
    ])
    # Re-verify rotation logic
    c, s = np.cos(rot_phi), np.sin(rot_phi)
    m_axis = np.array([
        m_base[0] * c - m_base[1] * s,
        m_base[0] * s + m_base[1] * c,
        m_base[2]
    ])
    
    # 2. Physics Update
    # Vectorized field calculation is hard for dipole, but let's try a chunked approach or just loop
    # Actually, let's use a hybrid: update a subset of particles or use NumPy broadcasting
    
    # Broadcasted field update (approximate)
    r_mag = np.linalg.norm(pos, axis=1, keepdims=True)
    r_mag = np.maximum(r_mag, 1.0)
    
    # dipole part
    dots = np.sum(pos * m_axis, axis=1, keepdims=True)
    B = (3 * dots * pos - m_axis * (r_mag**2)) / (r_mag**5)
    B_mag = np.sqrt(np.sum(B**2, axis=1, keepdims=True))
    B = np.where(B_mag > 1e-10, B / B_mag, 0)
    
    # toroidal part
    dist_xy = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2).reshape(-1, 1)
    twist = np.clip((dist_xy / LIGHT_CYLINDER), 0, 1.5)
    toroidal = np.zeros_like(pos)
    toroidal[:, 0] = -pos[:, 1]
    toroidal[:, 1] = pos[:, 0]
    tor_mag = np.sqrt(toroidal[:, 0]**2 + toroidal[:, 1]**2).reshape(-1, 1)
    toroidal = np.where(tor_mag > 1e-10, toroidal / tor_mag, 0)
    
    # Combine
    force = B + toroidal * twist * 1.8 
    
    # Add radial wind beyond light cylinder
    radial = pos / (r_mag + 1e-9)
    wind_factor = np.clip((dist_xy - LIGHT_CYLINDER) / 200.0, 0, 1)
    force += radial * wind_factor * 2.5
    
    # Update state
    # Particles follow force lines + slight diffusion/noise
    noise = np.random.standard_normal((NUM_PARTICLES, 3)) * 0.1
    vel = (force + noise) * 16.0 
    pos += vel
    age += 1
    
    # Reset dead or escaped particles
    reset_mask = (age >= PARTICLE_LIFESPAN) | (r_mag.flatten() > 1000)
    num_reset = np.sum(reset_mask)
    if num_reset > 0:
        indices = np.where(reset_mask)[0]
        # Re-seed in volume
        r_new = STAR_RADIUS * (1.0 + np.random.uniform(0, 3.0, num_reset))
        phi = np.random.uniform(0, 2 * np.pi, num_reset)
        theta = np.arccos(np.random.uniform(-1, 1, num_reset))
        pos[indices, 0] = r_new * np.sin(theta) * np.cos(phi)
        pos[indices, 1] = r_new * np.sin(theta) * np.sin(phi)
        pos[indices, 2] = r_new * np.cos(theta)
        age[indices] = 0
    
    # 3. Rendering
    py5.background(0)
    # No translate/rotate here since we did manual projection
    
    py5.blend_mode(py5.ADD)
    
    # Draw star core
    py5.no_stroke()
    py5.fill(60, 10, 100, 80) # White core
    # Project center
    z_center = -500 # Consistent with manual project
    f_center = 1200 / np.abs(z_center)
    py5.circle(py5.width/2, py5.height/2, STAR_RADIUS * 2 * f_center)
    
    # Draw Particles
    # Color by distance and age
    h_vals = (200 + 80 * np.clip(r_mag.flatten() / 800, 0, 1)) % 360 # Cyan to Purple
    
    # Manual Projection
    # Project 3D to 2D
    # move back, rotate
    cx, sx = np.cos(1.2), np.sin(1.2)
    rz = t * 0.003
    cz, sz = np.cos(rz), np.sin(rz)
    
    # Rotate Z
    px = pos[:, 0] * cz - pos[:, 1] * sz
    py = pos[:, 0] * sz + pos[:, 1] * cz
    pz = pos[:, 2]
    
    # Rotate X (oblique)
    py_final = py * cx - pz * sx
    pz_final = py * sx + pz * cx
    
    # Translate and Project
    z_final = pz_final - 500
    f = 1200 / (np.abs(z_final) + 1e-6)
    screen_x = px * f + py5.width/2
    screen_y = py_final * f + py5.height/2
    
    # Batch points by hue for performance
    num_buckets = 6
    for i in range(num_buckets):
        h_min = 200 + i * (80/num_buckets)
        h_max = h_min + (80/num_buckets)
        mask = (h_vals >= h_min) & (h_vals < h_max)
        if not np.any(mask): continue
        
        py5.stroke(h_min, 70, 100, 22)
        py5.stroke_weight(2.2)
        py5.points(np.stack([screen_x[mask], screen_y[mask]], axis=1))
    
    # 4. Save/Exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count % 10 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Encode video
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
