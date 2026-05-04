from pathlib import Path
import subprocess
import sys
import py5
import numpy as np
from scipy.ndimage import convolve

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 30 # Simulation is heavy, 30fps is smoother for RD
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Resolution (lower than screen for speed, upscaled in render)
SIM_SCALE = 4
W, H = SIZE[0] // SIM_SCALE, SIZE[1] // SIM_SCALE

# Gray-Scott Constants
DA, DB = 1.0, 0.5
F, K = 0.0545, 0.062 # Spirals/Neural pattern

# State
U = np.ones((H, W), dtype=np.float32)
V = np.zeros((H, W), dtype=np.float32)

# Laplacian Kernel
LAP_KERNEL = np.array([
    [0.05, 0.2, 0.05],
    [0.2, -1.0, 0.2],
    [0.05, 0.2, 0.05]
], dtype=np.float32)

def setup():
    global U, V
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial seeds
    center_x, center_y = W // 2, H // 2
    for _ in range(12):
        rx = center_x + np.random.randint(-W//4, W//4)
        ry = center_y + np.random.randint(-H//4, H//4)
        rad = np.random.randint(5, 15)
        U[ry-rad:ry+rad, rx-rad:rx+rad] = 0.5
        V[ry-rad:ry+rad, rx-rad:rx+rad] = 0.25

def draw():
    global U, V
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Update simulation (multiple steps per frame)
    for _ in range(12):
        lu = convolve(U, LAP_KERNEL, mode='wrap')
        lv = convolve(V, LAP_KERNEL, mode='wrap')
        
        uvv = U * V * V
        U += (DA * lu - uvv + F * (1 - U))
        V += (DB * lv + uvv - (F + K) * V)
        
        np.clip(U, 0, 1, out=U)
        np.clip(V, 0, 1, out=V)
        
    # Shading and Rendering
    # Compute Gradients for 3D Shading
    dy, dx = np.gradient(V)
    # Lighting: Light coming from top-left
    light_dir = np.array([-1, -1, 0.5])
    light_dir /= np.linalg.norm(light_dir)
    
    # Normal vector: (dx, dy, 0.1)
    normals = np.stack([dx, dy, np.ones_like(dx) * 0.05], axis=-1)
    norm_mags = np.linalg.norm(normals, axis=-1, keepdims=True)
    normals /= norm_mags
    
    # Lambertian diffuse
    diffuse = np.sum(normals * light_dir, axis=-1)
    diffuse = np.clip(diffuse, 0, 1)
    
    # Color mapping (V = Density)
    # Base Colors
    coral_pink = np.array([1.0, 0.5, 0.4])
    biolume_blue = np.array([0.0, 0.8, 0.9])
    
    # Mix based on V and diffuse
    color_field = np.zeros((H, W, 3))
    color_field += coral_pink * (V[:, :, np.newaxis] ** 1.5)
    color_field += biolume_blue * (1.0 - V[:, :, np.newaxis]) * 0.1
    
    # Apply Shading
    color_field *= (0.3 + 0.7 * diffuse[:, :, np.newaxis])
    
    # Upscale to Screen Pixels
    repeat_y = py5.pixel_height // H
    repeat_x = py5.pixel_width // W
    final_rgb = np.repeat(np.repeat(color_field, repeat_y, axis=0), repeat_x, axis=1)
    # Ensure exact match
    final_rgb = final_rgb[:py5.pixel_height, :py5.pixel_width]
    
    # Add bloom-like glow on V peaks
    glow = np.clip(V - 0.6, 0, 1) * 0.5
    glow_rgb = np.repeat(np.repeat(glow, repeat_y, axis=0), repeat_x, axis=1)
    glow_rgb = glow_rgb[:py5.pixel_height, :py5.pixel_width, np.newaxis]
    final_rgb += glow_rgb * biolume_blue
    
    py5.set_np_pixels((np.clip(final_rgb, 0, 1) * 255).astype(np.uint8), bands="RGB")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Preview
    if py5.frame_count == 1:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Update preview to a middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
