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

NUM_POINTS = 500000
STEPS_PER_FRAME = 3

# Particle coordinates
x = np.random.uniform(-2, 2, NUM_POINTS).astype(np.float32)
y = np.random.uniform(-2, 2, NUM_POINTS).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global x, y
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Clifford attractor parameters morphing over time
    # We smoothly interpolate parameters to explore different chaotic regimes
    a = py5.lerp(1.4, -1.7, (np.sin(t * np.pi * 2) + 1) / 2)
    b = py5.lerp(1.9, 1.8, (np.cos(t * np.pi * 2) + 1) / 2)
    c = py5.lerp(-1.2, -1.9, (np.sin(t * np.pi * 4) + 1) / 2)
    d = py5.lerp(-1.5, -0.4, (np.cos(t * np.pi * 4) + 1) / 2)
    
    # Fade out previous frame slightly
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Instead of drawing shapes, we directly manipulate pixels for extreme speed
    # We maintain a density map for the current frame
    density = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)
    
    for _ in range(STEPS_PER_FRAME):
        nx = np.sin(a * y) + c * np.cos(a * x)
        ny = np.sin(b * x) + d * np.cos(b * y)
        x[:] = nx
        y[:] = ny
        
        # Map to screen
        # Clifford bounds are generally [-3, 3]
        px = ((x + 2.5) / 5.0 * SIZE[0]).astype(int)
        py_ = ((y + 2.5) / 5.0 * SIZE[1]).astype(int)
        
        # Keep within bounds
        valid = (px >= 0) & (px < SIZE[0]) & (py_ >= 0) & (py_ < SIZE[1])
        px = px[valid]
        py_ = py_[valid]
        
        # Add to density map
        np.add.at(density, (py_, px), 1.0)
        
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Color mapping:
    # High density -> Bright Cyan / White
    # Low density -> Deep Magenta / Blue
    
    density_norm = np.clip(density * 0.5, 0, 255)
    
    # Base color buffer extraction
    curr_r = pixels[:, :, 1].astype(np.float32)
    curr_g = pixels[:, :, 2].astype(np.float32)
    curr_b = pixels[:, :, 3].astype(np.float32)
    
    # Additive colors
    # R: More magenta at low density, less at high
    add_r = density_norm * 0.8 + 20 * (density_norm > 0)
    # G: Cyan/white at high density
    add_g = density_norm * 1.5
    # B: Blue/magenta base, bright cyan at high density
    add_b = density_norm * 1.2 + 50 * (density_norm > 0)
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = np.clip(curr_r * 0.8 + add_r, 0, 255).astype(np.uint8)
    pixels[:, :, 2] = np.clip(curr_g * 0.8 + add_g, 0, 255).astype(np.uint8)
    pixels[:, :, 3] = np.clip(curr_b * 0.8 + add_b, 0, 255).astype(np.uint8)
    
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
            
        import os
        os._exit(0)

py5.run_sketch()
