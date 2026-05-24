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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 120000

# Base parameters
phases = np.random.uniform(0, 2*np.pi, NUM_PARTICLES)
radii = np.random.uniform(100, 450, NUM_PARTICLES)
colors = np.zeros((NUM_PARTICLES, 4), dtype=np.uint8)

# HSB to RGB mapping for coloring
# Magenta to Cyan
for i in range(NUM_PARTICLES):
    hue = np.random.uniform(0.5, 0.9)  # 0.5=cyan, 0.8=magenta
    colors[i, 0] = 255 # A
    if hue < 0.66: # cyan to blue
        colors[i, 1] = 0
        colors[i, 2] = int(255 * (0.66 - hue) / 0.16)
        colors[i, 3] = 255
    else: # blue to magenta
        colors[i, 1] = int(255 * (hue - 0.66) / 0.24)
        colors[i, 2] = 0
        colors[i, 3] = 255

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # We modulate the Lissajous frequencies over time to show decay to resonance
    # Start with complex irrational ratios, decay to 1:1:1
    fx = py5.lerp(3.14159, 1.0, t)
    fy = py5.lerp(2.71828, 1.0, t)
    fz = py5.lerp(1.61803, 1.0, t)
    
    # Calculate positions
    # Angle varies by phase and time
    angle = phases + t * 10.0
    
    x = radii * np.sin(angle * fx)
    y = radii * np.cos(angle * fy)
    z = radii * np.sin(angle * fz + np.pi/4)
    
    # Rotate the whole knot in 3D
    rot_y = t * np.pi * 2.0
    rot_x = t * np.pi
    
    # Simple manual rotation matrix for 3D
    cos_y, sin_y = np.cos(rot_y), np.sin(rot_y)
    cos_x, sin_x = np.cos(rot_x), np.sin(rot_x)
    
    # Rot Y
    x1 = x * cos_y - z * sin_y
    z1 = x * sin_y + z * cos_y
    
    # Rot X
    y2 = y * cos_x - z1 * sin_x
    z2 = y * sin_x + z1 * cos_x
    
    # Projection
    scale = 800.0 / (800.0 + z2)
    px = x1 * scale + py5.width / 2
    py = y2 * scale + py5.height / 2
    
    # Filter bounds
    valid = (px >= 0) & (px < py5.width) & (py >= 0) & (py < py5.height)
    
    # We can draw using py5.points() but we need to pack the colors
    # Actually, the fastest way in py5 for 100k points with color is setting the stroke 
    # individually, or using a shape. Since py5 doesn't easily vectorize stroke for points,
    # and np_pixels is fast in P2D but we are in P3D, let's use the shape approach or 
    # directly update np_pixels. In P3D, load_np_pixels() is available!
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # P3D np_pixels is also (H, W, 4) with ARGB on Mac, but let's carefully add to it
    p_x = px[valid].astype(int)
    p_y = py[valid].astype(int)
    c_r = colors[valid, 1].astype(np.uint16)
    c_g = colors[valid, 2].astype(np.uint16)
    c_b = colors[valid, 3].astype(np.uint16)
    
    curr_r = pixels[p_y, p_x, 1]
    curr_g = pixels[p_y, p_x, 2]
    curr_b = pixels[p_y, p_x, 3]
    
    new_r = np.clip(curr_r.astype(np.float32) + c_r * 0.15, 0, 255).astype(np.uint8)
    new_g = np.clip(curr_g.astype(np.float32) + c_g * 0.15, 0, 255).astype(np.uint8)
    new_b = np.clip(curr_b.astype(np.float32) + c_b * 0.15, 0, 255).astype(np.uint8)
    
    pixels[p_y, p_x, 0] = 255
    pixels[p_y, p_x, 1] = new_r
    pixels[p_y, p_x, 2] = new_g
    pixels[p_y, p_x, 3] = new_b
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
