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

# Spherical Curl Fluid Parameters
NUM_PARTICLES = 600000
STEPS_PER_FRAME = 2
DT = 0.5
RADIUS = 400.0

def scalar_potential(p, t):
    # p is (N, 3)
    x = p[:, 0]
    y = p[:, 1]
    z = p[:, 2]
    
    # Complex 3D sine wave interference pattern (acts as our noise)
    scale = 0.015
    s1 = np.sin(x * scale + t * 0.5) * np.cos(y * scale - t * 0.3)
    s2 = np.sin(y * scale * 1.5 - t * 0.4) * np.cos(z * scale * 1.5 + t * 0.6)
    s3 = np.sin(z * scale * 2.0 + t * 0.7) * np.cos(x * scale * 2.0 - t * 0.2)
    
    # Adding a polar vortex (strong flow at poles)
    polar = np.cos(np.arccos(z / RADIUS) * 3.0) * 0.5
    
    return s1 + s2 + s3 + polar

def get_velocity(p, t):
    # Numerical gradient
    eps = 1.0
    
    px = np.copy(p); px[:, 0] += eps
    mx = np.copy(p); mx[:, 0] -= eps
    dx = (scalar_potential(px, t) - scalar_potential(mx, t)) / (2.0 * eps)
    
    py = np.copy(p); py[:, 1] += eps
    my = np.copy(p); my[:, 1] -= eps
    dy = (scalar_potential(py, t) - scalar_potential(my, t)) / (2.0 * eps)
    
    pz = np.copy(p); pz[:, 2] += eps
    mz = np.copy(p); mz[:, 2] -= eps
    dz = (scalar_potential(pz, t) - scalar_potential(mz, t)) / (2.0 * eps)
    
    grad = np.column_stack((dx, dy, dz))
    
    # Normal to the sphere
    n = p / RADIUS
    
    # Velocity is grad x n (cross product)
    # This guarantees flow is tangent to sphere and divergence-free
    v = np.cross(grad, n)
    return v

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colormap
    
    # Distribute particles randomly on a sphere
    z = np.random.uniform(-1.0, 1.0, NUM_PARTICLES)
    phi = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    r = np.sqrt(1.0 - z*z)
    
    x = r * np.cos(phi)
    y = r * np.sin(phi)
    
    pos = np.column_stack((x, y, z)).astype(np.float32) * RADIUS
    
    # Gas Giant Colormap (Jupiter / Saturn vibes, but glowing and kinetic)
    # Deep Blue/Purple at equator, Gold/Orange at mid-latitudes, White at poles
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0 # represents abs(z)/RADIUS
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.3:
            p = v / 0.3
            colormap[i, 1:] = [int(p * 150), 0, 100 + int(p * 155)] # Blue/Purple
        elif v < 0.7:
            p = (v - 0.3) / 0.4
            colormap[i, 1:] = [150 + int(p * 105), int(p * 200), 255 - int(p * 200)] # Gold/Orange
        else:
            p = (v - 0.7) / 0.3
            colormap[i, 1:] = [255, 200 + int(p * 55), 55 + int(p * 200)] # Yellow/White

def step_physics(t):
    global pos
    
    v = get_velocity(pos, t)
    
    # Speed scalar
    speed = 15.0
    pos += v * speed * DT
    
    # Add thermal noise (Brownian motion)
    pos += np.random.uniform(-0.5, 0.5, (NUM_PARTICLES, 3))
    
    # Reproject to sphere
    mags = np.linalg.norm(pos, axis=1, keepdims=True)
    pos = (pos / mags) * RADIUS

def draw():
    global pos
    
    t = py5.frame_count * 0.01
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / deep fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 210 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation (slowly rotating the planet)
    cam_angle = t * 0.2
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    # Tilt the planet slightly
    tilt = 0.4
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    
    rot_x = pos[:, 0] * cos_c - pos[:, 2] * sin_c
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_c + pos[:, 2] * cos_c
    
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Filter out particles on the back of the sphere (rot_z2 > 0 is back, < 0 is front)
    # Actually, if we use rot_z2 > 0, they are further away. 
    # Let's say front is negative Z if camera is at -Z looking at origin.
    front_mask = rot_z2 < 50.0 
    
    # Project front particles
    fov = H * 1.5
    z_offset = 800.0
    Z = rot_z2[front_mask] + z_offset
    Z = np.where(Z < 10.0, 10.0, Z)
    
    screen_x = (rot_x[front_mask] * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y2[front_mask] * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Color based on latitude (original Z coordinate)
    latitudes = np.abs(pos[front_mask][valid, 2]) / RADIUS
    intensity = np.clip(latitudes * 255.0, 0, 255).astype(np.uint8)
    
    # Edge fading (fade out particles near the limb of the sphere)
    # rot_z2 is close to 0 at the limb
    z_vals = rot_z2[front_mask][valid]
    edge_fade = np.clip((50.0 - z_vals) / 50.0, 0.0, 1.0)
    
    vr = (colormap[intensity, 1] * edge_fade).astype(np.uint8)
    vg = (colormap[intensity, 2] * edge_fade).astype(np.uint8)
    vb = (colormap[intensity, 3] * edge_fade).astype(np.uint8)
    
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
