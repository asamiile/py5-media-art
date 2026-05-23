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

NUM_BLOBS = 60
blobs = np.zeros((NUM_BLOBS, 5)) # x, y, dx, dy, radius

gradient_graphics = None

def create_gradient(radius):
    g = py5.create_graphics(radius*2, radius*2)
    g.begin_draw()
    g.color_mode(py5.HSB, 360, 100, 100, 100)
    g.no_stroke()
    # Draw radial gradient
    for r in range(radius, 0, -2):
        alpha = py5.remap(r, 0, radius, 100, 0)
        # Using a grayscale gradient to act as a density field
        g.fill(0, 0, 100, alpha)
        g.circle(radius, radius, r*2)
    g.end_draw()
    return g

def setup():
    global gradient_graphics, blobs
    # Must use P2D to allow fast pixel manipulation via py5.np_pixels
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    gradient_graphics = create_gradient(150)
    
    # Initialize blobs
    blobs[:, 0] = np.random.uniform(0, py5.width, NUM_BLOBS)
    blobs[:, 1] = np.random.uniform(0, py5.height, NUM_BLOBS)
    blobs[:, 2] = np.random.uniform(-4, 4, NUM_BLOBS)
    blobs[:, 3] = np.random.uniform(-4, 4, NUM_BLOBS)
    blobs[:, 4] = np.random.uniform(80, 250, NUM_BLOBS) # scale factors
    
def draw():
    global blobs
    
    # 1. Draw the density field
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.image_mode(py5.CENTER)
    
    t = py5.frame_count * 0.05
    
    # Update and draw blobs
    for i in range(NUM_BLOBS):
        # Add some swarming noise to velocity
        blobs[i, 2] += py5.sin(blobs[i, 1] * 0.01 + t) * 0.2
        blobs[i, 3] += py5.cos(blobs[i, 0] * 0.01 + t) * 0.2
        
        blobs[i, 0] += blobs[i, 2]
        blobs[i, 1] += blobs[i, 3]
        
        # Bounce off walls
        if blobs[i, 0] < 0 or blobs[i, 0] > py5.width: blobs[i, 2] *= -1
        if blobs[i, 1] < 0 or blobs[i, 1] > py5.height: blobs[i, 3] *= -1
        
        # Draw gradient image, scaled by blob radius
        s = blobs[i, 4]
        py5.image(gradient_graphics, blobs[i, 0], blobs[i, 1], s, s)
        
    # 2. Threshold the density field using NumPy to create sharp metaballs
    py5.blend_mode(py5.BLEND)
    py5.load_np_pixels()
    
    # py5.np_pixels is an array of shape (height, width, 4) in ARGB format.
    # We will extract the blue channel (index 3 in ARGB? Actually it's A=0, R=1, G=2, B=3)
    # Since we drew in grayscale, all channels have the same density value.
    density = py5.np_pixels[:, :, 1] # Read Red channel
    
    # Create mask where density > threshold
    threshold = 120
    mask_inside = density > threshold
    mask_edge = (density > threshold - 20) & (density <= threshold)
    
    # Clear the screen in memory
    py5.np_pixels[:, :, :] = 0 # Transparent black
    
    # Color the inside (Liquid Core)
    py5.np_pixels[mask_inside, 0] = 255 # A
    py5.np_pixels[mask_inside, 1] = 0   # R
    py5.np_pixels[mask_inside, 2] = 255 # G
    py5.np_pixels[mask_inside, 3] = 255 # B (Cyan liquid)
    
    # Color the edge (Neon Outline)
    py5.np_pixels[mask_edge, 0] = 255 # A
    py5.np_pixels[mask_edge, 1] = 255 # R
    py5.np_pixels[mask_edge, 2] = 0   # G
    py5.np_pixels[mask_edge, 3] = 255 # B (Magenta edge)
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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
