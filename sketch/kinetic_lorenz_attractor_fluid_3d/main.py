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

# Lorenz Attractor Parameters
NUM_PARTICLES = 600000
STEPS_PER_FRAME = 3
DT = 0.003

sigma = 10.0
beta = 8.0 / 3.0
# rho will be animated

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colormap
    
    # Initialize particles near the attractor's standard range
    # x: -20 to 20, y: -20 to 20, z: 0 to 50
    pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    pos[:, 0] = np.random.uniform(-20, 20, NUM_PARTICLES)
    pos[:, 1] = np.random.uniform(-20, 20, NUM_PARTICLES)
    pos[:, 2] = np.random.uniform(0, 50, NUM_PARTICLES)
    
    # Colormap: Z-height mapping
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        # Deep Blue -> Cyan -> White -> Orange -> Red
        if v < 0.25:
            p = v / 0.25
            colormap[i, 1:] = [0, int(p * 150), 100 + int(p * 155)]
        elif v < 0.5:
            p = (v - 0.25) / 0.25
            colormap[i, 1:] = [int(p * 255), 150 + int(p * 105), 255]
        elif v < 0.75:
            p = (v - 0.5) / 0.25
            colormap[i, 1:] = [255, 255 - int(p * 100), 255 - int(p * 255)]
        else:
            p = (v - 0.75) / 0.25
            colormap[i, 1:] = [255, 155 - int(p * 155), 0]

def step_physics(t):
    global pos
    
    # Animate rho to make the butterfly "breathe"
    rho = 28.0 + 8.0 * np.sin(t * 0.5)
    
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]
    
    # Runge-Kutta 2 (Midpoint) or just Euler. Euler is fine for very small DT.
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    
    # Brownian noise to give the strange attractor volume (Langevin dynamics)
    # This prevents all particles from collapsing into a 1D line over time
    pos += np.random.uniform(-0.02, 0.02, (NUM_PARTICLES, 3))

def draw():
    global pos
    
    t = py5.frame_count * 0.016
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / deep fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 235 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation
    # Rotate around the Z-axis (which is the vertical axis of the Lorenz attractor)
    # But for a good view, we also tilt the camera slightly.
    cam_angle = t * 0.4
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    # Center of the attractor is roughly at z=rho-1 (around z=27), x=0, y=0
    # Relocate to origin for rotation
    p_rel = np.copy(pos)
    p_rel[:, 2] -= 27.0
    
    # Rotate around Z
    rot_x = p_rel[:, 0] * cos_c - p_rel[:, 1] * sin_c
    rot_y = p_rel[:, 0] * sin_c + p_rel[:, 1] * cos_c
    rot_z = p_rel[:, 2]
    
    # Tilt forward slightly (rotate around X)
    tilt = 0.3
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection
    fov = H * 2.0
    z_offset = 60.0 # Distance to camera
    Z = rot_z2 + z_offset
    Z = np.where(Z < 1.0, 1.0, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    # Invert Y to match screen coordinates (Y goes down)
    screen_y = (-rot_y2 * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Color based on absolute Z height of the particle (before camera rotation)
    z_height = pos[valid, 2]
    intensity = np.clip((z_height / 50.0) * 255.0, 0, 255).astype(np.uint8)
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((120.0 - Z[valid]) / 100.0, 0.1, 1.0)
    
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
