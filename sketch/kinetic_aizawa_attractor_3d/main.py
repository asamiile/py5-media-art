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

# Aizawa Attractor Parameters
NUM_PARTICLES = 600000
STEPS_PER_FRAME = 3
DT = 0.02

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colormap
    
    # Initialize particles near the origin
    pos = np.random.uniform(-0.1, 0.1, (NUM_PARTICLES, 3)).astype(np.float32)
    
    # Generate a fiery "Plasma" Colormap (Deep Purple -> Magenta -> Orange -> Yellow)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.33:
            p = v / 0.33
            colormap[i, 1:] = [int(p * 150), 0, int(p * 200)] # Dark Purple
        elif v < 0.66:
            p = (v - 0.33) / 0.33
            colormap[i, 1:] = [150 + int(p * 105), int(p * 100), 200 - int(p * 150)] # Magenta/Red
        else:
            p = (v - 0.66) / 0.34
            colormap[i, 1:] = [255, 100 + int(p * 155), 50 + int(p * 100)] # Orange/Yellow

def step_physics(t):
    global pos
    
    # Aizawa Attractor base parameters
    a = 0.95
    c = 0.6
    e = 0.25
    
    # Modulate d and f over time to make the attractor "breathe" and twist
    d = 3.5 + 0.5 * np.sin(t * 0.4)
    f = 0.1 + 0.05 * np.cos(t * 0.3)
    
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]
    
    # Aizawa Attractor differential equations
    dx = (z - 0.7) * x - d * y
    dy = d * x + (z - 0.7) * y
    dz = c + a * z - (z**3) / 3.0 - (x**2 + y**2) * (1.0 + e * z) + f * z * (x**3)
    
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    
    # Langevin noise to thicken the infinitely thin 1D chaotic orbit into a 3D fluid volume
    pos += np.random.uniform(-0.015, 0.015, (NUM_PARTICLES, 3))

def draw():
    global pos
    
    t = py5.frame_count * 0.02
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / deep space fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 230 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation
    cam_angle = t * 0.1
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    # Rotate around Y axis
    rot_x = pos[:, 0] * cos_c - pos[:, 2] * sin_c
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_c + pos[:, 2] * cos_c
    
    # Tilt slightly to look down into the vortex tube
    tilt = 0.6
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection
    fov = H * 0.5 # Aizawa bounds are small (~[-2, 2]), so zoom in
    z_offset = 5.0
    Z = rot_z2 + z_offset
    Z = np.where(Z < 0.5, 0.5, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y2 * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Color based on height (Z-axis originally, giving the tornado a fiery core)
    # The Aizawa attractor usually ranges from z=0 to z=2
    intensity = np.clip((pos[valid, 2] / 2.0) * 255.0, 0, 255).astype(np.uint8)
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((8.0 - Z[valid]) / 6.0, 0.1, 1.0)
    
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
