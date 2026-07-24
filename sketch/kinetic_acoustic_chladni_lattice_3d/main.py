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

# 3D Chladni Parameters
NUM_PARTICLES = 600000
STEPS_PER_FRAME = 3
DT = 0.05
BOX_SIZE = 15.0

def get_vibration(x, y, z, t):
    # Frequencies morphing over time
    A = 1.0 + 0.5 * np.sin(t * 0.3)
    B = 1.5 + 0.5 * np.cos(t * 0.4)
    C = 2.0 + 0.5 * np.sin(t * 0.5)
    
    # 3D standing wave equation (cyclically symmetric interference)
    v1 = np.sin(A * x) * np.cos(B * y) * np.sin(C * z)
    v2 = np.sin(B * x) * np.cos(C * y) * np.sin(A * z)
    v3 = np.sin(C * x) * np.cos(A * y) * np.sin(B * z)
    
    return v1 + v2 + v3

def get_force(p, t):
    # We want particles to gather at the NODES where vibration is ZERO.
    # Therefore, potential energy is proportional to V^2.
    # Force = -Gradient(V^2) = -2 * V * Gradient(V)
    
    eps = 0.01
    
    # Evaluate base V
    V = get_vibration(p[:,0], p[:,1], p[:,2], t)
    
    # Evaluate gradients
    dx = (get_vibration(p[:,0] + eps, p[:,1], p[:,2], t) - get_vibration(p[:,0] - eps, p[:,1], p[:,2], t)) / (2.0 * eps)
    dy = (get_vibration(p[:,0], p[:,1] + eps, p[:,2], t) - get_vibration(p[:,0], p[:,1] - eps, p[:,2], t)) / (2.0 * eps)
    dz = (get_vibration(p[:,0], p[:,1], p[:,2] + eps, t) - get_vibration(p[:,0], p[:,1], p[:,2] - eps, t)) / (2.0 * eps)
    
    grad_V = np.column_stack((dx, dy, dz))
    
    # F = -2 * V * grad(V)
    # Adding a scaling factor for aesthetics
    return -2.0 * V[:, np.newaxis] * grad_V * 5.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colormap
    
    # Init uniformly in a 3D box
    pos = np.random.uniform(-BOX_SIZE, BOX_SIZE, (NUM_PARTICLES, 3)).astype(np.float32)
    vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    
    # Platinum / Gold Chladni Colormap
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.4:
            p = v / 0.4
            colormap[i, 1:] = [int(p * 150), int(p * 140), int(p * 100)] # Dark Bronze
        elif v < 0.8:
            p = (v - 0.4) / 0.4
            colormap[i, 1:] = [150 + int(p * 105), 140 + int(p * 115), 100 + int(p * 100)] # Gold
        else:
            p = (v - 0.8) / 0.2
            colormap[i, 1:] = [255, 255, 200 + int(p * 55)] # Platinum / White

def step_physics(t):
    global pos, vel
    
    F = get_force(pos, t)
    
    vel += F * DT
    
    # Friction is critical so they settle in the nodes instead of oscillating infinitely
    vel *= 0.90
    
    # Add strong thermal noise to keep them flowing around the lattice instead of freezing
    vel += np.random.uniform(-0.8, 0.8, (NUM_PARTICLES, 3))
    
    pos += vel * DT
    
    # Confine to box
    pos = np.clip(pos, -BOX_SIZE, BOX_SIZE)

def draw():
    global pos, vel
    
    t = py5.frame_count * 0.02
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / deep fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 230 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation
    cam_angle = t * 0.2
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    rot_x = pos[:, 0] * cos_c - pos[:, 2] * sin_c
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_c + pos[:, 2] * cos_c
    
    # Tilt
    tilt = 0.5
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection
    fov = H * 1.5
    z_offset = 35.0
    Z = rot_z2 + z_offset
    Z = np.where(Z < 1.0, 1.0, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y2 * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Color based on depth (Z-axis originally) to highlight the 3D structure
    intensity = np.clip(((pos[valid, 2] + BOX_SIZE) / (2.0 * BOX_SIZE)) * 255.0, 0, 255).astype(np.uint8)
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((50.0 - Z[valid]) / 30.0, 0.1, 1.0)
    
    vr = (colormap[intensity, 1] * depth_fade).astype(np.uint8)
    vg = (colormap[intensity, 2] * depth_fade).astype(np.uint8)
    vb = (colormap[intensity, 3] * depth_fade).astype(np.uint8)
    
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
