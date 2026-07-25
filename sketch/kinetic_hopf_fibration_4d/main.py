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

# Hopf Fibration Parameters
NUM_PARTICLES = 1000000
STEPS_PER_FRAME = 1

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global theta1, theta2, colormap
    
    # Uniformly distribute points on the 2D surface of a Clifford Torus in 4D
    theta1 = np.random.uniform(0, 2*np.pi, NUM_PARTICLES).astype(np.float32)
    theta2 = np.random.uniform(0, 2*np.pi, NUM_PARTICLES).astype(np.float32)
    
    # Add a slight noise to give the "fibers" some volume (like a fluid)
    global noise1, noise2
    noise1 = np.random.normal(0, 0.05, NUM_PARTICLES).astype(np.float32)
    noise2 = np.random.normal(0, 0.05, NUM_PARTICLES).astype(np.float32)
    
    # 4D Colormap (Neon Pink -> Cyan -> Purple)
    # We will map theta1 + theta2 to the colormap
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.33:
            p = v / 0.33
            colormap[i, 1:] = [255 - int(p * 255), int(p * 255), 255] # Pink to Cyan
        elif v < 0.66:
            p = (v - 0.33) / 0.33
            colormap[i, 1:] = [int(p * 150), 255 - int(p * 255), 255] # Cyan to Purple
        else:
            p = (v - 0.66) / 0.34
            colormap[i, 1:] = [150 + int(p * 105), 0, 255] # Purple to Pink

def draw():
    global theta1, theta2
    
    t = py5.frame_count * 0.02
    
    # Flow the particles along the torus surface to make it kinetic
    theta1 = (theta1 + 0.015) % (2 * np.pi)
    theta2 = (theta2 - 0.008) % (2 * np.pi)
    
    # Include noise for volume
    t1 = theta1 + noise1
    t2 = theta2 + noise2
    
    # 4D Coordinates of the Clifford Torus
    # (cos(t1), sin(t1), cos(t2), sin(t2))
    # Note: normally this lies on the unit 3-sphere S^3 in R^4 if we scale by 1/sqrt(2)
    scale = 1.0 / np.sqrt(2.0)
    X = np.cos(t1) * scale
    Y = np.sin(t1) * scale
    Z = np.cos(t2) * scale
    W = np.sin(t2) * scale
    
    # Apply 4D Rotations
    # Rotate in X-W plane
    alpha = t * 0.5
    ca, sa = np.cos(alpha), np.sin(alpha)
    X2 = X * ca - W * sa
    W2 = X * sa + W * ca
    
    # Rotate in Y-Z plane
    beta = t * 0.3
    cb, sb = np.cos(beta), np.sin(beta)
    Y2 = Y * cb - Z * sb
    Z2 = Y * sb + Z * cb
    
    # Stereographic Projection from 4D to 3D
    # The projection pole is at W = 1. We use 1.2 to avoid singularity and keep it contained
    proj_scale = 1.0 / (1.2 - W2)
    x_3d = X2 * proj_scale
    y_3d = Y2 * proj_scale
    z_3d = Z2 * proj_scale
    
    py5.load_np_pixels()
    
    # Motion blur / deep fade
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 220 // 256).astype(np.uint8)
    
    W_scr, H_scr = SIZE
    
    # 3D Camera Rotation (Spinning around the 3D projected shape)
    cam_angle = t * 0.4
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    rot_x = x_3d * cos_c - z_3d * sin_c
    rot_y = y_3d
    rot_z = x_3d * sin_c + z_3d * cos_c
    
    # Tilt slightly
    tilt = 0.5
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection to 2D screen
    fov = H_scr * 1.5
    z_offset = 6.0
    Z_cam = rot_z2 + z_offset
    Z_cam = np.where(Z_cam < 0.1, 0.1, Z_cam)
    
    screen_x = (rot_x * (fov / Z_cam) + W_scr / 2).astype(np.int32)
    screen_y = (rot_y2 * (fov / Z_cam) + H_scr / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W_scr) & (screen_y >= 0) & (screen_y < H_scr)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Color mapping based on the intrinsic 4D surface coordinates
    color_phase = (theta1[valid] + theta2[valid] * 2.0) / (6.0 * np.pi)
    color_phase = color_phase % 1.0
    intensity = (color_phase * 255).astype(np.uint8)
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((12.0 - Z_cam[valid]) / 10.0, 0.05, 1.0)
    
    vr = (colormap[intensity, 1] * depth_fade).astype(np.uint8)
    vg = (colormap[intensity, 2] * depth_fade).astype(np.uint8)
    vb = (colormap[intensity, 3] * depth_fade).astype(np.uint8)
    
    flat_indices = sy * W_scr + sx
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
