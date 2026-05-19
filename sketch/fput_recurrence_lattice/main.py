from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# FPUT Simulation Parameters
N = 32
alpha = 0.23  # Non-linear coupling strength
beta = 0.00   # Pure alpha-FPUT lattice
A = 5.5       # Initial fundamental amplitude
dt = 0.02
substeps = 22

# State variables
q = np.zeros(N, dtype=np.float32)
v = np.zeros(N, dtype=np.float32)
i_idx = np.arange(N, dtype=np.float32)

# Initial fundamental mode excitation
q = A * np.sin(np.pi * i_idx / (N - 1))
q[0] = 0.0
q[-1] = 0.0

# Precomputed sine projection matrix for Fourier modes
sin_matrix = np.zeros((4, N), dtype=np.float32)
for k in range(1, 5):
    sin_matrix[k - 1] = np.sin(k * np.pi * i_idx / (N - 1))

# 100,000 Helix tracer particles
num_helix_particles = 100000
helix_u = np.random.uniform(0.0, 1.0, num_helix_particles).astype(np.float32)
helix_strand = np.random.choice([0, 1], num_helix_particles).astype(np.int32)
helix_offsets = np.random.uniform(-np.pi, np.pi, num_helix_particles).astype(np.float32)

# 50,000 Background orbital particles
num_orbit_particles = 50000
orbit_theta = np.random.uniform(0, 2 * np.pi, num_orbit_particles).astype(np.float32)
orbit_ring = np.random.choice([0, 1, 2, 3], num_orbit_particles, p=[0.35, 0.25, 0.22, 0.18]).astype(np.int32)
orbit_wobble = np.random.uniform(-10.0, 10.0, num_orbit_particles).astype(np.float32)

# Smooth modes for visual stability
smooth_A1 = A
smooth_A2 = 0.0
smooth_A3 = 0.0
smooth_A4 = 0.0

def setup():
    py5.size(SIZE[0], SIZE[1], py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(8, 8, 10)  # Near-black obsidian

def draw():
    global q, v, smooth_A1, smooth_A2, smooth_A3, smooth_A4
    
    # Elegant dark-decay background for rich trailing highlights
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(8, 8, 10, 15)  # Restrained decay for silken trails
    py5.rect(0, 0, py5.width, py5.height)
    
    # 1. Integrate FPUT System
    for _ in range(substeps):
        dq_right = np.roll(q, -1) - q
        dq_left = q - np.roll(q, 1)
        
        # Dirichlet boundaries
        dq_right[-1] = 0.0 - q[-1]
        dq_left[0] = q[0] - 0.0
        
        acc = (dq_right - dq_left) + alpha * (dq_right**2 - dq_left**2)
        acc[0] = 0.0
        acc[-1] = 0.0
        
        # Velocity Verlet step
        q_next = q + v * dt + 0.5 * acc * dt**2
        
        dq_right_next = np.roll(q_next, -1) - q_next
        dq_left_next = q_next - np.roll(q_next, 1)
        dq_right_next[-1] = 0.0 - q_next[-1]
        dq_left_next[0] = q_next[0] - 0.0
        
        acc_next = (dq_right_next - dq_left_next) + alpha * (dq_right_next**2 - dq_left_next**2)
        acc_next[0] = 0.0
        acc_next[-1] = 0.0
        
        v = v + 0.5 * (acc + acc_next) * dt
        q = q_next

    # Calculate Modal Amplitudes (Fourier projections)
    # Mode k: Sum q_i * sin(k * pi * i / (N-1))
    A_modes = np.abs(np.dot(sin_matrix, q))
    A1, A2, A3, A4 = A_modes[0], A_modes[1], A_modes[2], A_modes[3]
    
    # Smoothing filter
    smooth_A1 = 0.92 * smooth_A1 + 0.08 * A1
    smooth_A2 = 0.92 * smooth_A2 + 0.08 * A2
    smooth_A3 = 0.92 * smooth_A3 + 0.08 * A3
    smooth_A4 = 0.92 * smooth_A4 + 0.08 * A4
    
    total_high = smooth_A2 + smooth_A3 + smooth_A4
    recurrence_ratio = smooth_A1 / (smooth_A1 + total_high + 1e-5)
    
    # Rotation angles
    t = py5.frame_count * 0.004
    rot_y = py5.frame_count * 0.007
    rot_x = py5.frame_count * 0.003
    
    # Dynamic camera positioning
    camera_dist = 850.0 + np.sin(t) * 50.0
    screen_scale = 1100.0
    
    # 2. Render Helix Tracer Particles
    # Map high-mode energy to dispersion (thermal noise)
    dispersion = 2.0 + 36.0 * (1.0 - recurrence_ratio)
    
    # Interpolate displacement along the helix curve
    x_nodes = helix_u * (N - 1)
    q_interp = np.interp(x_nodes, np.arange(N), q)
    
    # 3D Helix coordinate generation
    theta = t * 2.0 + 4.0 * np.pi * helix_u + helix_strand * np.pi
    R = 170.0 + q_interp * 32.0
    
    # Add thermal perturbation based on dispersion
    noise_r = np.random.normal(0.0, dispersion, num_helix_particles)
    noise_z = np.random.normal(0.0, dispersion, num_helix_particles)
    R += noise_r
    
    X = R * np.cos(theta)
    Y = R * np.sin(theta)
    Z = -320.0 + 640.0 * helix_u + noise_z
    
    # 3D Rotations
    cos_y, sin_y = np.cos(rot_y), np.sin(rot_y)
    x1 = X * cos_y - Z * sin_y
    z1 = X * sin_y + Z * cos_y
    
    cos_x, sin_x = np.cos(rot_x), np.sin(rot_x)
    y2 = Y * cos_x - z1 * sin_x
    z2 = Y * sin_x + z1 * cos_x
    
    # Projection
    proj_x = py5.width / 2.0 + x1 * screen_scale / (z2 + camera_dist)
    proj_y = py5.height / 2.0 + y2 * screen_scale / (z2 + camera_dist)
    
    # Clip off-screen
    valid = (proj_x >= 0) & (proj_x < py5.width) & (proj_y >= 0) & (proj_y < py5.height) & (z2 + camera_dist > 50)
    px = proj_x[valid]
    py = proj_y[valid]
    pz = z2[valid]
    pu = helix_u[valid]
    
    # 3. Render Background Orbital Rings (visualize hidden energy Fourier modes)
    orbit_theta_shifted = orbit_theta + py5.frame_count * 0.003 * (orbit_ring + 1)
    
    base_r = [320.0, 360.0, 400.0, 440.0]
    amps = [smooth_A1, smooth_A2, smooth_A3, smooth_A4]
    
    # Orbital Ring positions
    r_orbit = np.array([base_r[r] + amps[r] * 8.0 for r in orbit_ring], dtype=np.float32)
    ox = py5.width / 2.0 + (r_orbit + orbit_wobble) * np.cos(orbit_theta_shifted)
    oy = py5.height / 2.0 + (r_orbit + orbit_wobble) * np.sin(orbit_theta_shifted)
    
    valid_orbit = (ox >= 0) & (ox < py5.width) & (oy >= 0) & (oy < py5.height)
    ox_p = ox[valid_orbit]
    oy_p = oy[valid_orbit]
    or_ring = orbit_ring[valid_orbit]
    
    # Start Additive Point Rendering
    py5.blend_mode(py5.ADD)
    
    # Draw Background Orbital Particles by Ring (Mode color maps)
    # Ring 0 (Mode 1): Electric Cyan
    r0 = or_ring == 0
    py5.stroke(0, 240, 255, int(18.0 * recurrence_ratio + 5.0))
    py5.stroke_weight(1.0)
    py5.points(np.stack([ox_p[r0], oy_p[r0]], axis=-1))
    
    # Ring 1 (Mode 2): Royal Purple
    r1 = or_ring == 1
    py5.stroke(189, 0, 255, int(15.0 * (1.0 - recurrence_ratio) + 5.0))
    py5.stroke_weight(1.0)
    py5.points(np.stack([ox_p[r1], oy_p[r1]], axis=-1))
    
    # Ring 2 (Mode 3): Vibrant Pink
    r2 = or_ring == 2
    py5.stroke(255, 0, 170, int(14.0 * (1.0 - recurrence_ratio) + 4.0))
    py5.stroke_weight(1.0)
    py5.points(np.stack([ox_p[r2], oy_p[r2]], axis=-1))
    
    # Ring 3 (Mode 4): Amber/Gold
    r3 = or_ring == 3
    py5.stroke(255, 220, 100, int(12.0 * (1.0 - recurrence_ratio) + 4.0))
    py5.stroke_weight(1.0)
    py5.points(np.stack([ox_p[r3], oy_p[r3]], axis=-1))
    
    # Draw Helix Particles (color mapped by local displacement/modes)
    # Group by recurrence index and depth for beautiful volumetric shading
    depth_norm = (pz - np.min(pz)) / (np.max(pz) - np.min(pz) + 1e-5)
    
    # Group 1: Pristine Fundamental (Coherence) - High Recurrence Ratio
    # Colored in bright Ice Blue / Cyan
    g1 = (recurrence_ratio > 0.6)
    px_g1, py_g1 = px[g1], py[g1]
    dn_g1 = depth_norm[g1]
    
    # Sort into 3 depth bins for realistic 3D feel
    for db in range(3):
        bin_mask = (dn_g1 >= db/3.0) & (dn_g1 < (db+1)/3.0)
        alpha_val = int((20 + db * 25) * recurrence_ratio)
        py5.stroke(0, 240, 255, alpha_val)
        py5.stroke_weight(1.0 + db * 0.5)
        py5.points(np.stack([px_g1[bin_mask], py_g1[bin_mask]], axis=-1))
        
    # Group 2: Excited Thermalized Mode (Amethyst/Magenta) - Mid/Low Recurrence Ratio
    g2 = (~g1)
    px_g2, py_g2 = px[g2], py[g2]
    dn_g2 = depth_norm[g2]
    
    for db in range(3):
        bin_mask = (dn_g2 >= db/3.0) & (dn_g2 < (db+1)/3.0)
        # Shift color from amethyst to pink based on depth/excitation
        py5.stroke(170 + db * 20, 0, 255, int(12 + db * 16))
        py5.stroke_weight(1.0 + db * 0.5)
        py5.points(np.stack([px_g2[bin_mask], py_g2[bin_mask]], axis=-1))
        
    # Coherence Flash / Core Recombination Highlight
    # Blinding gold/white core when recurrence_ratio is extremely high
    if recurrence_ratio > 0.85:
        flash_mask = (pu > 0.4) & (pu < 0.6) & (pz > -100) & (pz < 100)
        if np.any(flash_mask):
            py5.stroke(255, 248, 220, int(60 * (recurrence_ratio - 0.85) / 0.15))
            py5.stroke_weight(3.0)
            py5.points(np.stack([px[flash_mask], py[flash_mask]], axis=-1))
            
    # Draw simple modal HUD overlay at the bottom for mathematical flavor
    py5.blend_mode(py5.BLEND)
    py5.no_fill()
    py5.stroke(255, 255, 255, 20)
    py5.stroke_weight(1.0)
    
    # Save frames for rendering
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save preview snapshot (frame at 50% duration)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save disk space
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
