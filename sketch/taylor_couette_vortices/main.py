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

# Simulation Parameters
num_particles = 120000
Ri = 125.0
Ro = 225.0
d = Ro - Ri
k_z = np.pi / 100.0  # Torus height = 100
U0 = 4.5
V0 = 2.2
Omega_i = 1.6
Omega_o = -0.2
m_waves = 5
omega_w = 0.06

# Particle States
p_r = np.random.uniform(Ri, Ro, num_particles).astype(np.float32)
p_theta = np.random.uniform(0, 2 * np.pi, num_particles).astype(np.float32)
p_z = np.random.uniform(-300.0, 300.0, num_particles).astype(np.float32)

def setup():
    py5.size(SIZE[0], SIZE[1], py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 7)  # Deep obsidian black

def draw():
    global p_r, p_theta, p_z
    
    # Decaying trail effect for fluid flow visuality
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 7, 20)  # Gentle decay trails
    py5.rect(0, 0, py5.width, py5.height)
    
    # 1. Calculate time-varying physical state
    t_sec = py5.frame_count / 60.0
    
    # Wave amplitude aw transitions:
    # 0s -> 4s: aw = 0 (perfect stacked toroidal vortices)
    # 4s -> 10s: aw rises to 1.2 (wavy vortex flow)
    # 10s -> 13s: aw = 1.2 + turbulent chaotic noise
    # 13s -> 15s: aw decreases back to 0 for a seamless loop
    if t_sec < 4.0:
        aw = 0.0
        turbulence = 0.0
    elif t_sec < 10.0:
        aw = 1.2 * (t_sec - 4.0) / 6.0
        turbulence = 0.0
    elif t_sec < 13.0:
        aw = 1.2
        # Introduce high-frequency turbulent shear noise
        turbulence = 0.15 * np.sin(t_sec * np.pi * 8.0)
    else:
        aw = 1.2 * (15.0 - t_sec) / 2.0
        turbulence = 0.0
        
    dt_sim = 0.18
    
    # 2. Physics Advection step (vectorized)
    x_gap = (p_r - Ri) / d
    wave_phase = aw * np.sin(m_waves * p_theta - omega_w * py5.frame_count)
    
    # Velocity field calculations
    u_r = U0 * np.sin(np.pi * x_gap) * np.cos(k_z * p_z - wave_phase)
    u_z = -U0 * np.cos(np.pi * x_gap) * np.sin(k_z * p_z - wave_phase)
    
    # Azimuthal velocity with background shear + vortex advection
    u_theta_bg = Omega_i * Ri * (1.0 - x_gap) + Omega_o * Ro * x_gap
    u_theta = u_theta_bg + V0 * np.sin(np.pi * x_gap) * np.cos(k_z * p_z - wave_phase)
    
    # Add optional high-shear turbulence
    if turbulence > 0.0:
        u_r += np.random.normal(0.0, U0 * turbulence, num_particles)
        u_z += np.random.normal(0.0, U0 * turbulence, num_particles)
        u_theta += np.random.normal(0.0, V0 * turbulence, num_particles)
        
    # Integrate using Euler-Maruyama
    p_r += u_r * dt_sim
    p_theta += (u_theta / p_r) * dt_sim
    p_z += u_z * dt_sim
    
    # Boundary Conditions
    # Radial: clamp and bounce slightly
    p_r = np.clip(p_r, Ri + 1.0, Ro - 1.0)
    
    # Vertical: periodic boundary wrap
    p_z = -300.0 + (p_z + 300.0) % 600.0
    
    # 3. 3D Cartesian coordinates
    X = p_r * np.cos(p_theta)
    Y = p_r * np.sin(p_theta)
    Z = p_z
    
    # Rotation (fixed tilted X-axis + slowly orbiting Y-axis)
    rot_x = 0.45
    rot_y = py5.frame_count * 0.0065
    
    # Rotate around Y
    cos_y, sin_y = np.cos(rot_y), np.sin(rot_y)
    x1 = X * cos_y - Z * sin_y
    z1 = X * sin_y + Z * cos_y
    
    # Rotate around X
    cos_x, sin_x = np.cos(rot_x), np.sin(rot_x)
    y2 = Y * cos_x - z1 * sin_x
    z2 = Y * sin_x + z1 * cos_x
    
    # 3D projection onto 2D viewport
    camera_dist = 850.0
    if turbulence > 0.0:
        # Volumetric camera shudder proportional to high-shear turbulence
        camera_dist += np.random.normal(0.0, 9.0) * (turbulence / 0.15)
    screen_scale = 1150.0
    proj_x = py5.width / 2.0 + x1 * screen_scale / (z2 + camera_dist)
    proj_y = py5.height / 2.0 + y2 * screen_scale / (z2 + camera_dist)
    
    # Clip particles off-screen
    valid = (proj_x >= 0) & (proj_x < py5.width) & (proj_y >= 0) & (proj_y < py5.height) & (z2 + camera_dist > 50)
    px = proj_x[valid]
    py = proj_y[valid]
    pz = z2[valid]
    pr = p_r[valid]
    
    # Normalize depth for shading and transparency
    z_min, z_max = np.min(pz), np.max(pz)
    depth_norm = (pz - z_min) / (z_max - z_min + 1e-5)
    
    # 4. Color Mapping
    # Inside cylinder region: Molten Amber/Copper (Orange)
    # Outside cylinder region: Deep Cobalt Blue
    # Sheared region (center of gap): Electrical White/Cyan
    # Normalize radial position (0 -> Ri, 1 -> Ro)
    rad_norm = (pr - Ri) / d
    
    # Set up points for additive rendering
    py5.blend_mode(py5.ADD)
    
    # We segment particles into 3 color charge regions for efficient drawing:
    # 1. Inner (rad_norm < 0.35) -> Amber/Orange
    # 2. Middle (0.35 <= rad_norm < 0.65) -> Electric Cyan / White
    # 3. Outer (rad_norm >= 0.65) -> Cobalt Blue
    
    # Group 1: Inner region (Molten Copper/Amber)
    c1 = (rad_norm < 0.38)
    px_c1, py_c1 = px[c1], py[c1]
    dn_c1 = depth_norm[c1]
    
    # Volumetric shading based on depth
    for db in range(3):
        bin_mask = (dn_c1 >= db/3.0) & (dn_c1 < (db+1)/3.0)
        # Deep orange to glowing yellow/gold highlights
        alpha = int(12.0 + db * 16.0)
        py5.stroke(255, 100 + db * 45, 10, alpha)
        py5.stroke_weight(1.0 + db * 0.5)
        py5.points(np.stack([px_c1[bin_mask], py_c1[bin_mask]], axis=-1))
        
    # Group 2: Middle shear boundary (Electric White/Cyan)
    c2 = (rad_norm >= 0.38) & (rad_norm < 0.68)
    px_c2, py_c2 = px[c2], py[c2]
    dn_c2 = depth_norm[c2]
    
    for db in range(3):
        bin_mask = (dn_c2 >= db/3.0) & (dn_c2 < (db+1)/3.0)
        # Deep cyan to blinding electric white in the foreground
        alpha = int(14.0 + db * 18.0)
        py5.stroke(140 + db * 45, 230 + db * 12, 255, alpha)
        py5.stroke_weight(1.0 + db * 0.5)
        py5.points(np.stack([px_c2[bin_mask], py_c2[bin_mask]], axis=-1))
        
    # Group 3: Outer boundary (Cobalt Blue / Prussian Blue)
    c3 = (rad_norm >= 0.68)
    px_c3, py_c3 = px[c3], py[c3]
    dn_c3 = depth_norm[c3]
    
    for db in range(3):
        bin_mask = (dn_c3 >= db/3.0) & (dn_c3 < (db+1)/3.0)
        # Deep space blue to vibrant neon cobalt
        alpha = int(10.0 + db * 14.0)
        py5.stroke(15 * db, 70 + db * 35, 255, alpha)
        py5.stroke_weight(1.0 + db * 0.5)
        py5.points(np.stack([px_c3[bin_mask], py_c3[bin_mask]], axis=-1))
        
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
        
        # Save preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
