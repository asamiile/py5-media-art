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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 150000
dt = 0.5
G = 100.0 # Gravitational constant scaled for visual

positions = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
velocities = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)

# Initialize particles in a large disk
radii = np.random.uniform(50, 400, NUM_PARTICLES)
angles = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
heights = np.random.normal(0, 5, NUM_PARTICLES)

positions[:, 0] = np.cos(angles) * radii
positions[:, 2] = np.sin(angles) * radii
positions[:, 1] = heights

# Initial velocities for circular orbit v = sqrt(GM/r)
# We have two masses, but approximate with one combined mass at center for initial velocities
M_total = 2000.0
v_mag = np.sqrt(G * M_total / radii)
velocities[:, 0] = -np.sin(angles) * v_mag
velocities[:, 2] = np.cos(angles) * v_mag

# Introduce some noise to velocities
velocities += np.random.normal(0, 0.5, (NUM_PARTICLES, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    global positions, velocities
    
    # Trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.02
    
    # Binary black hole positions
    orbit_r = 50.0
    bh1 = np.array([np.cos(time_val)*orbit_r, 0, np.sin(time_val)*orbit_r])
    bh2 = np.array([-np.cos(time_val)*orbit_r, 0, -np.sin(time_val)*orbit_r])
    M1, M2 = 1000.0, 1000.0
    
    # Calculate gravity forces
    # Force from BH1
    d1 = bh1 - positions
    dist1_sq = np.sum(d1**2, axis=1) + 100.0 # Softening parameter
    dist1 = np.sqrt(dist1_sq)
    f1_mag = (G * M1) / dist1_sq
    f1 = (d1 / dist1[:, np.newaxis]) * f1_mag[:, np.newaxis]
    
    # Force from BH2
    d2 = bh2 - positions
    dist2_sq = np.sum(d2**2, axis=1) + 100.0
    dist2 = np.sqrt(dist2_sq)
    f2_mag = (G * M2) / dist2_sq
    f2 = (d2 / dist2[:, np.newaxis]) * f2_mag[:, np.newaxis]
    
    # Update velocities and positions
    velocities += (f1 + f2) * dt
    positions += velocities * dt
    
    # Event horizon (destroy and respawn particles that get too close)
    too_close = (dist1 < 10) | (dist2 < 10) | (np.sum(positions**2, axis=1) > 1000000)
    if np.any(too_close):
        num_respawn = np.sum(too_close)
        new_radii = np.random.uniform(350, 400, num_respawn)
        new_angles = np.random.uniform(0, 2 * np.pi, num_respawn)
        positions[too_close, 0] = np.cos(new_angles) * new_radii
        positions[too_close, 2] = np.sin(new_angles) * new_radii
        positions[too_close, 1] = np.random.normal(0, 5, num_respawn)
        
        new_v_mag = np.sqrt(G * M_total / new_radii)
        velocities[too_close, 0] = -np.sin(new_angles) * new_v_mag
        velocities[too_close, 2] = np.cos(new_angles) * new_v_mag
        velocities[too_close, 1] = 0
    
    # 3D Rotation for rendering (isometric/tilted view)
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(0.5), -np.sin(0.5)],
        [0, np.sin(0.5), np.cos(0.5)]
    ])
    
    rot_y = np.array([
        [np.cos(time_val*0.2), 0, np.sin(time_val*0.2)],
        [0, 1, 0],
        [-np.sin(time_val*0.2), 0, np.cos(time_val*0.2)]
    ])
    
    rotated = positions.dot(rot_y).dot(rot_x)
    
    # Perspective projection
    fov = 800.0
    z_offset = rotated[:, 2] + 600.0
    valid_z = z_offset > 1
    
    proj_x = (rotated[valid_z, 0] / z_offset[valid_z]) * fov + py5.width / 2
    proj_y = (rotated[valid_z, 1] / z_offset[valid_z]) * fov + py5.height / 2
    
    # Color by speed (blueshift / redshift proxy)
    speed = np.sqrt(np.sum(velocities**2, axis=1))[valid_z]
    
    # Draw
    py5.stroke_weight(2.0)
    
    # Very fast particles (White / Cyan)
    fast_mask = speed > 15.0
    if np.any(fast_mask):
        py5.stroke(180, 50, 100, 40)
        py5.points(np.column_stack((proj_x[fast_mask], proj_y[fast_mask])))
        
    # Medium particles (Orange / Yellow)
    med_mask = (speed <= 15.0) & (speed > 5.0)
    if np.any(med_mask):
        py5.stroke(30, 80, 100, 20)
        py5.points(np.column_stack((proj_x[med_mask], proj_y[med_mask])))
        
    # Slow particles (Deep Red)
    slow_mask = speed <= 5.0
    if np.any(slow_mask):
        py5.stroke(0, 90, 60, 10)
        py5.points(np.column_stack((proj_x[slow_mask], proj_y[slow_mask])))

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
