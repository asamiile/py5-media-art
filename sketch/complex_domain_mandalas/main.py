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

# Precompute the coordinate grid
W, H = SIZE
x = np.linspace(-3.5, 3.5, W, dtype=np.float32)
y = np.linspace(-3.5 * H / W, 3.5 * H / W, H, dtype=np.float32)
X, Y = np.meshgrid(x, y)
Z_base = X + 1j * Y

def cosine_palette(t, a, b, c, d):
    """IQ's cosine palette: a, b, c, d are 3-element arrays."""
    t_exp = t[..., None]
    res = a + b * np.cos(6.28318 * (c * t_exp + d))
    return np.clip(res, 0.0, 1.0)

# Palette params (Pearlescent, Sapphire, Amber)
# We will construct a custom palette
pal_a = np.array([0.2, 0.3, 0.5], dtype=np.float32)
pal_b = np.array([0.8, 0.6, 0.4], dtype=np.float32)
pal_c = np.array([1.0, 1.0, 1.0], dtype=np.float32)
pal_d = np.array([0.0, 0.15, 0.30], dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    t = py5.frame_count / 60.0
    
    # Dynamic parameters
    a = 0.6 + 0.2 * np.sin(t * 0.7) + 1j * 0.45
    b = -0.35 + 1j * (0.22 + 0.15 * np.cos(t * 0.8))
    c = 0.18 - 1j * 0.38
    d = 0.8 + 1j * 0.15 * np.sin(t * 0.9)
    
    # Transformation: Z^3 - 1 modulated by a mobius-like rotation
    # To create a "zoom" effect, we can scale Z
    zoom = 1.0 + 0.5 * np.sin(t * 0.4)
    Z = Z_base * zoom
    
    # Complex function
    Z_mapped = (a * Z**3 + b) / (c * Z**2 + d)
    
    phase = np.angle(Z_mapped)
    mag = np.abs(Z_mapped)
    
    # Map to colors
    # Normalised phase 0 to 1
    phase_norm = (phase + np.pi) / (2 * np.pi)
    
    # Create smooth contour lines from magnitude
    contour = np.abs((np.log1p(mag) * 5.0) % 1.0 - 0.5) * 2.0
    contour = contour ** 2.0  # sharpen
    
    # Create phase lines
    phase_lines = np.abs((phase_norm * 12.0) % 1.0 - 0.5) * 2.0
    phase_lines = phase_lines ** 4.0
    
    # Base color from palette
    color_val = cosine_palette(phase_norm + t * 0.1, pal_a, pal_b, pal_c, pal_d)
    
    # Darken based on magnitude to create obsidian void
    mag_fade = 1.0 / (1.0 + mag**2)
    
    # Combine
    final_color = color_val * (0.4 + 0.6 * contour[..., None])
    final_color *= (0.6 + 0.4 * phase_lines[..., None])
    final_color *= mag_fade[..., None]
    
    # Add a warm amber glow to the phase lines near the poles
    amber = np.array([1.0, 0.6, 0.1], dtype=np.float32)
    glow = phase_lines * (1.0 - contour) * mag_fade
    final_color += amber * glow[..., None] * 0.5
    
    # Convert to ARGB for py5
    final_color = np.clip(final_color * 255, 0, 255).astype(np.uint8)
    
    # Create the ARGB integer array
    alpha = np.full((H, W, 1), 255, dtype=np.uint8)
    argb = np.concatenate((alpha, final_color), axis=-1)
    
    py5.load_np_pixels()
    py5.np_pixels[:] = argb
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
