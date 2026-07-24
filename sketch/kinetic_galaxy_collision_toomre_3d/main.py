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

# Toomre Galaxy Collision Parameters
NUM_STARS = 600000
STEPS_PER_FRAME = 6
DT = 0.02
G = 1000.0
M1 = 100.0
M2 = 100.0

def generate_galaxy(center, mass, num_stars, normal, radius_range):
    # Generate stars in a disk
    r = np.random.uniform(radius_range[0], radius_range[1], num_stars)
    theta = np.random.uniform(0, 2 * np.pi, num_stars)
    
    # Local coordinates (flat in XY plane)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.random.uniform(-1, 1, num_stars) * (r * 0.02) # Slight thickness
    
    pos_local = np.column_stack((x, y, z))
    
    # Keplerian velocity v = sqrt(G*M/r)
    v_mag = np.sqrt(G * mass / r)
    vx = -v_mag * np.sin(theta)
    vy =  v_mag * np.cos(theta)
    vz = np.zeros(num_stars)
    vel_local = np.column_stack((vx, vy, vz))
    
    # Rotate disk to align Z-axis with 'normal'
    # Simplified approach: Just apply a random 3D rotation matrix
    # Normal is passed as Euler angles (rx, ry)
    rx, ry = normal
    
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    
    Ry = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    
    R = Ry @ Rx
    
    pos_rotated = pos_local @ R.T
    vel_rotated = vel_local @ R.T
    
    pos_rotated += center
    
    return pos_rotated.astype(np.float32), vel_rotated.astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, c1_pos, c1_vel, c2_pos, c2_vel, colors
    
    W, H = SIZE
    
    # Core 1 (Cyan Galaxy)
    c1_pos = np.array([-400.0, -200.0, -100.0])
    c1_vel = np.array([3.5, 2.0, 1.0])
    pos1, vel1 = generate_galaxy(c1_pos, M1, NUM_STARS // 2, (0.5, 0.2), (30, 250))
    
    # Core 2 (Magenta Galaxy)
    c2_pos = np.array([400.0, 200.0, 100.0])
    c2_vel = np.array([-3.5, -2.0, -1.0])
    pos2, vel2 = generate_galaxy(c2_pos, M2, NUM_STARS // 2, (-0.6, 0.4), (20, 200))
    
    pos = np.vstack((pos1, pos2))
    vel = np.vstack((vel1, vel2))
    
    # Add initial systemic velocity to stars
    vel[:NUM_STARS//2] += c1_vel
    vel[NUM_STARS//2:] += c2_vel
    
    # Colors
    colors = np.zeros((NUM_STARS, 3), dtype=np.uint8)
    
    # Galaxy 1 (Cyan/Blue)
    r1 = np.linalg.norm(pos1 - c1_pos, axis=1)
    # Hot blue core, cyan outer
    colors[:NUM_STARS//2, 0] = np.clip(100 - r1, 0, 255) # R
    colors[:NUM_STARS//2, 1] = np.clip(255 - r1*0.5, 0, 255) # G
    colors[:NUM_STARS//2, 2] = 255 # B
    
    # Galaxy 2 (Magenta/Orange)
    r2 = np.linalg.norm(pos2 - c2_pos, axis=1)
    # Hot white/yellow core, magenta/orange outer
    colors[NUM_STARS//2:, 0] = 255 # R
    colors[NUM_STARS//2:, 1] = np.clip(200 - r2, 0, 255) # G
    colors[NUM_STARS//2:, 2] = np.clip(150 - r2, 0, 255) # B

def step_physics():
    global pos, vel, c1_pos, c1_vel, c2_pos, c2_vel
    
    # 1. Update Cores (2-body problem)
    r12 = c2_pos - c1_pos
    dist12 = np.linalg.norm(r12) + 10.0 # Softening
    f_mag = G * M1 * M2 / (dist12**2)
    dir12 = r12 / dist12
    
    a1 = dir12 * (f_mag / M1)
    a2 = -dir12 * (f_mag / M2)
    
    c1_vel += a1 * DT
    c2_vel += a2 * DT
    c1_pos += c1_vel * DT
    c2_pos += c2_vel * DT
    
    # 2. Update Stars (Massless, attracted to Cores)
    # From Core 1
    d1 = c1_pos - pos
    dist1_sq = np.sum(d1*d1, axis=1, keepdims=True) + 400.0 # Softening
    dist1 = np.sqrt(dist1_sq)
    a_stars_1 = (G * M1 / dist1_sq) * (d1 / dist1)
    
    # From Core 2
    d2 = c2_pos - pos
    dist2_sq = np.sum(d2*d2, axis=1, keepdims=True) + 400.0
    dist2 = np.sqrt(dist2_sq)
    a_stars_2 = (G * M2 / dist2_sq) * (d2 / dist2)
    
    vel += (a_stars_1 + a_stars_2) * DT
    pos += vel * DT

def draw():
    global pos, vel
    
    for _ in range(STEPS_PER_FRAME):
        step_physics()
        
    py5.load_np_pixels()
    
    # Deep space fade (long trails)
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 230 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation (Slowly panning around the collision)
    t = py5.frame_count * 0.003
    cos_t, sin_t = np.cos(t), np.sin(t)
    
    # Center of mass tracking
    com = (c1_pos * M1 + c2_pos * M2) / (M1 + M2)
    
    # Relocate to origin for rotation
    p_rel = pos - com
    
    rot_x = p_rel[:, 0] * cos_t - p_rel[:, 2] * sin_t
    rot_y = p_rel[:, 1]
    rot_z = p_rel[:, 0] * sin_t + p_rel[:, 2] * cos_t
    
    # Perspective projection
    fov = H * 1.5
    z_offset = 600.0
    Z = rot_z + z_offset
    Z = np.where(Z < 10.0, 10.0, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y * (fov / Z) + H / 2).astype(np.int32)
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((1200.0 - Z) / 1000.0, 0.1, 1.0)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    vr = (colors[valid, 0] * depth_fade[valid]).astype(np.uint8)
    vg = (colors[valid, 1] * depth_fade[valid]).astype(np.uint8)
    vb = (colors[valid, 2] * depth_fade[valid]).astype(np.uint8)
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    flat_pixels[flat_indices, 1] = np.clip(flat_pixels[flat_indices, 1].astype(np.uint16) + vr, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 2] = np.clip(flat_pixels[flat_indices, 2].astype(np.uint16) + vg, 0, 255).astype(np.uint8)
    flat_pixels[flat_indices, 3] = np.clip(flat_pixels[flat_indices, 3].astype(np.uint16) + vb, 0, 255).astype(np.uint8)
    
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
