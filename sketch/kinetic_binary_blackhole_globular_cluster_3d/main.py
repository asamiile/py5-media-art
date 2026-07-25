from pathlib import Path
import shutil
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# N-Body Parameters
NUM_STARS = 2000000
STEPS_PER_FRAME = 4
DT = 0.005

# Physics Constants
G = 1.0
M_CLUSTER = 1000.0
A_PLUMMER = 2.0
M_BH = 300.0 # Mass of each black hole
BH_ORBIT_RADIUS = 0.8
BH_ORBIT_SPEED = 2.5
SOFTENING = 0.1

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colors
    
    # Init positions using a pseudo-Plummer distribution
    # r = a * (u^(-2/3) - 1)^(-1/2) where u is uniform(0,1)
    u = np.random.uniform(0.01, 1.0, NUM_STARS)
    r = A_PLUMMER / np.sqrt(u**(-2.0/3.0) - 1.0)
    
    # Random spherical directions
    z = np.random.uniform(-1.0, 1.0, NUM_STARS)
    phi = np.random.uniform(0, 2*np.pi, NUM_STARS)
    r_xy = np.sqrt(1.0 - z**2)
    
    x = r_xy * np.cos(phi)
    y = r_xy * np.sin(phi)
    
    pos = np.column_stack((x, y, z)).astype(np.float32) * r[:, np.newaxis]
    
    # Init velocities for circular orbits (Keplerian) + random dispersion
    # v = sqrt(G * M(r) / r)
    # For plummer, M(r) = M_CLUSTER * r^3 / (r^2 + a^2)^(3/2)
    m_r = M_CLUSTER * (r**3) / ((r**2 + A_PLUMMER**2)**1.5)
    v_circ = np.sqrt(G * m_r / (r + 1e-5))
    
    # Velocity vector perpendicular to r (assuming rotation around Z axis)
    # cross product of r and (0,0,1)
    v_dir = np.column_stack((-y, x, np.zeros_like(z)))
    v_norm = np.linalg.norm(v_dir, axis=1, keepdims=True) + 1e-5
    v_dir /= v_norm
    
    # Add random isotropic velocity dispersion for a realistic "hot" cluster
    dispersion = np.random.normal(0, 1.0, (NUM_STARS, 3)).astype(np.float32) * (v_circ[:, np.newaxis] * 0.3)
    
    vel = (v_dir * v_circ[:, np.newaxis] + dispersion).astype(np.float32)
    
    # Star Colors (Blue/White hot stars, Red dwarfs, Golden giants)
    # Map color to initial distance from center (core = blue, halo = red)
    colors = np.zeros((NUM_STARS, 3), dtype=np.uint8)
    core_mask = r < A_PLUMMER
    halo_mask = r >= A_PLUMMER
    
    colors[core_mask] = [20, 40, 100] # Bright Blue (additive)
    colors[halo_mask] = [80, 40, 10]  # Golden/Red
    
    # Add some ultra-bright white stars scattered
    white_mask = np.random.random(NUM_STARS) < 0.05
    colors[white_mask] = [150, 150, 150]

def step_physics(t):
    global pos, vel
    
    # Black Hole positions (orbiting each other in the XY plane)
    bh1_pos = np.array([np.cos(t * BH_ORBIT_SPEED) * BH_ORBIT_RADIUS, 
                        np.sin(t * BH_ORBIT_SPEED) * BH_ORBIT_RADIUS, 
                        0.0], dtype=np.float32)
    bh2_pos = -bh1_pos
    
    # Globular Cluster Mean Field Force (Plummer potential)
    r_sq = np.sum(pos**2, axis=1, keepdims=True)
    f_cluster = - (G * M_CLUSTER) / ((r_sq + A_PLUMMER**2)**1.5) * pos
    
    # BH 1 Force
    d1 = pos - bh1_pos
    r1_sq = np.sum(d1**2, axis=1, keepdims=True)
    f_bh1 = - (G * M_BH) / ((r1_sq + SOFTENING**2)**1.5) * d1
    
    # BH 2 Force
    d2 = pos - bh2_pos
    r2_sq = np.sum(d2**2, axis=1, keepdims=True)
    f_bh2 = - (G * M_BH) / ((r2_sq + SOFTENING**2)**1.5) * d2
    
    # Update
    acc = f_cluster + f_bh1 + f_bh2
    vel += acc * DT
    pos += vel * DT

def draw():
    global pos, colors
    
    t_global = py5.frame_count * 0.05
    for _ in range(STEPS_PER_FRAME):
        # We need a continuous time variable for the physics step
        # that advances by DT for the BH orbits
        # Actually t_global is just for the current frame
        t_phys = (py5.frame_count - 1) * STEPS_PER_FRAME * DT + _ * DT
        step_physics(t_phys)
        
    py5.load_np_pixels()
    
    # Deep space fade (motion blur)
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 200 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation (slow pan around the cluster)
    cam_angle = t_global * 0.1
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    rot_x = pos[:, 0] * cos_c - pos[:, 2] * sin_c
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_c + pos[:, 2] * cos_c
    
    # Tilt the galaxy
    tilt = 0.5
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection
    fov = H * 1.5
    z_offset = 12.0 # Pull camera back
    Z = rot_z2 + z_offset
    Z = np.where(Z < 0.1, 0.1, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y2 * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((25.0 - Z[valid]) / 20.0, 0.05, 1.0)
    
    # Get colors for valid points
    vc = colors[valid]
    
    vr = (vc[:, 0] * depth_fade).astype(np.uint8)
    vg = (vc[:, 1] * depth_fade).astype(np.uint8)
    vb = (vc[:, 2] * depth_fade).astype(np.uint8)
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    np.add.at(flat_pixels[:, 1], flat_indices, vr)
    np.add.at(flat_pixels[:, 2], flat_indices, vg)
    np.add.at(flat_pixels[:, 3], flat_indices, vb)
    
    # Clamp to 255
    flat_pixels[:, 1:] = np.clip(flat_pixels[:, 1:], 0, 255)
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

py5.run_sketch()
