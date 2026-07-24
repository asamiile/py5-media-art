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

NUM_POINTS = 300000
DT = 0.05
B_PARAM = 0.208186

def setup():
    py5.size(*SIZE) # Native 2D renderer for maximum stability
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos
    
    # Initialize points in a tight Gaussian cluster around origin
    pos = np.random.normal(0, 0.5, (NUM_POINTS, 3))
    
def draw():
    global pos
    
    W, H = SIZE
    
    # Update physics (Thomas Attractor)
    # dx/dt = sin(y) - bx
    # dy/dt = sin(z) - by
    # dz/dt = sin(x) - bz
    
    dx = np.sin(pos[:, 1]) - B_PARAM * pos[:, 0]
    dy = np.sin(pos[:, 2]) - B_PARAM * pos[:, 1]
    dz = np.sin(pos[:, 0]) - B_PARAM * pos[:, 2]
    
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    
    # 3D Rotation (Turntable animation)
    theta = py5.frame_count * 0.005
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    
    rot_x = pos[:, 0] * cos_t - pos[:, 2] * sin_t
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_t + pos[:, 2] * cos_t
    
    # Perspective projection
    fov = H * 0.6
    z_offset = 8.0 # Push back into screen
    Z = rot_z + z_offset
    
    # Avoid division by zero
    Z = np.where(Z < 0.1, 0.1, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y * (fov / Z) + H / 2).astype(np.int32)
    
    # Calculate depth-based brightness and color
    # Z range is roughly [3, 13]
    # We map Z to RGB values directly
    depth_norm = np.clip((Z - 3) / 10.0, 0, 1) # 0 = close, 1 = far
    
    # Close = Cyan/White, Far = Deep Blue
    r = (255 * (1.0 - depth_norm)**2).astype(np.uint8)
    g = (255 * (1.0 - depth_norm)).astype(np.uint8)
    b = np.full(NUM_POINTS, 255, dtype=np.uint8)
    
    # Fade previous frame
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Simple alpha fade (multiply by 0.92 ~ 235/256)
    # Using float scaling is slow, integer math is faster
    # py5.np_pixels shape is (H, W, 4) containing ARGB
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 235 // 256).astype(np.uint8)
    
    # Keep alpha 255
    pixels[:, :, 0] = 255
    
    # Draw points directly to pixel array
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    
    sx = screen_x[valid]
    sy = screen_y[valid]
    vr = r[valid]
    vg = g[valid]
    vb = b[valid]
    
    # For additive blending, we can't easily vectorize without Advanced Indexing accumulating correctly.
    # np.add.at can do this, but it's slower. Simple assignment is usually fine for dense point clouds, 
    # but since it's glowing smoke, additive is best.
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Numpy advanced indexing for simple assignment (last one wins if duplicate, but it's fast)
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
