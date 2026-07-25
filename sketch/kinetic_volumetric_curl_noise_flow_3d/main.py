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

NUM_POINTS = 500000
SPEED = 0.05
SCALE = 2.0 # Field scale

def setup():
    py5.size(*SIZE) # Native 2D renderer for maximum stability
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colors
    
    # Initialize points in a sphere
    r = np.random.uniform(0, 5, NUM_POINTS)
    theta = np.random.uniform(0, py5.TWO_PI, NUM_POINTS)
    phi = np.random.uniform(0, py5.PI, NUM_POINTS)
    
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    
    pos = np.column_stack((x, y, z))
    
    # Pre-calculate base colors based on initial position (mostly radius)
    colors = np.zeros((NUM_POINTS, 3), dtype=np.uint8)
    
    # Palette: Volumetric nebula (Magenta, Purple, Cyan)
    normalized_r = r / 5.0
    colors[:, 0] = (255 * (1 - normalized_r)).astype(np.uint8) # R
    colors[:, 1] = (50 * normalized_r).astype(np.uint8)        # G
    colors[:, 2] = (255 * normalized_r).astype(np.uint8)       # B
    
def draw():
    global pos
    
    W, H = SIZE
    t = py5.frame_count * 0.02
    
    # Update physics: Fast mathematical volumetric flow
    # Approximates curl noise via trigonometric interference
    px = pos[:, 0] * SCALE
    py = pos[:, 1] * SCALE
    pz = pos[:, 2] * SCALE
    
    vx = np.sin(py * 1.21 + t) * np.cos(pz * 0.83 - t*0.5) + np.sin(py * 0.5)
    vy = np.sin(pz * 1.13 - t) * np.cos(px * 0.97 + t*0.3) + np.cos(pz * 0.5)
    vz = np.sin(px * 1.37 + t) * np.cos(py * 0.71 - t*0.7) - np.sin(px * 0.5)
    
    # Add strong rotational vortex around origin to keep them together
    # vortex = cross(pos, (0, 1, 0)) = (-z, 0, x)
    vortex_strength = 0.5 / (np.linalg.norm(pos, axis=1) + 1.0)
    vx -= pos[:, 2] * vortex_strength
    vy += np.sin(pos[:, 1] * 0.5) * 0.1 # Gentle vertical drift
    vz += pos[:, 0] * vortex_strength
    
    pos[:, 0] += vx * SPEED
    pos[:, 1] += vy * SPEED
    pos[:, 2] += vz * SPEED
    
    # 3D Rotation (Turntable animation)
    # Rotate around Y axis
    theta_cam = py5.frame_count * 0.003
    cos_t = np.cos(theta_cam)
    sin_t = np.sin(theta_cam)
    
    rot_x = pos[:, 0] * cos_t - pos[:, 2] * sin_t
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_t + pos[:, 2] * cos_t
    
    # Perspective projection
    fov = H * 0.8
    z_offset = 12.0 # Push back into screen
    Z = rot_z + z_offset
    
    # Avoid division by zero
    Z = np.where(Z < 0.1, 0.1, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y * (fov / Z) + H / 2).astype(np.int32)
    
    # Depth-based alpha/brightness (Z range roughly [2, 22])
    depth_fade = np.clip((22.0 - Z) / 20.0, 0, 1) # 1 = close, 0 = far
    depth_fade = depth_fade * depth_fade # exponential falloff
    
    # Fade previous frame
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Multiply by 0.90 to fade (approx 230/256)
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 230 // 256).astype(np.uint8)
    pixels[:, :, 0] = 255 # Keep alpha 255
    
    # Draw points directly to pixel array
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Modulate color by depth fade
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
