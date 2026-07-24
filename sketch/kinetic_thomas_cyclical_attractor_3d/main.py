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

# Thomas Attractor Parameters
NUM_PARTICLES = 600000
STEPS_PER_FRAME = 3
DT = 0.05

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colormap
    
    # Initialize particles in a 3D box
    pos = np.random.uniform(-5.0, 5.0, (NUM_PARTICLES, 3)).astype(np.float32)
    
    # Pre-generate a Cyberpunk Neon Colormap (Cyan -> Magenta -> Yellow/White)
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.5:
            p = v / 0.5
            colormap[i, 1:] = [int(p * 255), int(255 - p * 255), 255] # Cyan (0,255,255) to Magenta (255,0,255)
        else:
            p = (v - 0.5) / 0.5
            colormap[i, 1:] = [255, int(p * 255), int(255 - p * 150)] # Magenta to Yellow/White

def step_physics(t):
    global pos
    
    # Parameter b oscillates slowly to change the fractal structure
    # b around 0.19 is highly chaotic, b > 0.22 is more structured
    b = 0.19 + 0.02 * np.sin(t * 0.5)
    
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]
    
    # Thomas Cyclically Symmetric Attractor
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    
    # Langevin noise to thicken the lines into a fluid volume
    pos += np.random.uniform(-0.01, 0.01, (NUM_PARTICLES, 3))

def draw():
    global pos
    
    t = py5.frame_count * 0.02
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Motion blur / deep fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 235 // 256).astype(np.uint8)
    
    W, H = SIZE
    
    # 3D Camera Rotation (Spinning around all axes since it's cyclically symmetric)
    cam_angle = t * 0.3
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    # Rotate Y
    rot_x = pos[:, 0] * cos_c - pos[:, 2] * sin_c
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_c + pos[:, 2] * cos_c
    
    # Rotate X
    tilt = cam_angle * 0.5
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection
    fov = H * 1.0
    z_offset = 12.0 # Distance to camera (attractor is ~[-5,5])
    Z = rot_z2 + z_offset
    Z = np.where(Z < 1.0, 1.0, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y2 * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Color based on distance from the origin (creating concentric color shells)
    dist = np.sqrt(pos[valid, 0]**2 + pos[valid, 1]**2 + pos[valid, 2]**2)
    intensity = np.clip((dist / 6.0) * 255.0, 0, 255).astype(np.uint8)
    
    # Depth fading
    depth_fade = np.clip((20.0 - Z[valid]) / 15.0, 0.1, 1.0)
    
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
