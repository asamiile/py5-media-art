import numpy as np
import scipy.ndimage as nd
from pathlib import Path
import subprocess
import sys
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

# Simulation resolution (1/4 of OUTPUT_SIZE)
SIM_W, SIM_H = SIZE[0] // 4, SIZE[1] // 4

# Gray-Scott parameters
Da, Db = 1.0, 0.5
f, k = 0.055, 0.062 # Biological Turing pattern
# Chiral advection strength
chiral_strength = 0.5

A = np.ones((SIM_H, SIM_W), dtype=np.float32)
B = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Seed initial pattern
cx, cy = SIM_W // 2, SIM_H // 2
r = 20
y, x = np.ogrid[-cy:SIM_H-cy, -cx:SIM_W-cx]
mask = x*x + y*y <= r*r
B[mask] = 1.0
A[mask] = 0.5

# Add some noise to break symmetry
A += np.random.uniform(-0.01, 0.01, (SIM_H, SIM_W)).astype(np.float32)
B += np.random.uniform(-0.01, 0.01, (SIM_H, SIM_W)).astype(np.float32)

laplacian_kernel = np.array([[0.05, 0.2, 0.05],
                             [0.2, -1.0, 0.2],
                             [0.05, 0.2, 0.05]], dtype=np.float32)

grad_y_kernel = np.array([[-1, -2, -1],
                          [ 0,  0,  0],
                          [ 1,  2,  1]], dtype=np.float32) / 8.0

grad_x_kernel = np.array([[-1,  0,  1],
                          [-2,  0,  2],
                          [-1,  0,  1]], dtype=np.float32) / 8.0

def step():
    global A, B
    
    # Calculate Laplacians
    lapA = nd.convolve(A, laplacian_kernel, mode='wrap')
    lapB = nd.convolve(B, laplacian_kernel, mode='wrap')
    
    # Calculate gradients for chiral advection
    gradA_x = nd.convolve(A, grad_x_kernel, mode='wrap')
    gradA_y = nd.convolve(A, grad_y_kernel, mode='wrap')
    gradB_x = nd.convolve(B, grad_x_kernel, mode='wrap')
    gradB_y = nd.convolve(B, grad_y_kernel, mode='wrap')
    
    # Chiral advection: Advect A by grad B rotated by 90 degrees, and B by grad A
    advA = chiral_strength * (gradA_x * gradB_y - gradA_y * gradB_x)
    advB = chiral_strength * (gradB_x * gradA_y - gradB_y * gradA_x)
    
    # Reaction
    reaction = A * B * B
    
    # Modulate feed/kill slightly across space for varied patterns
    # F and K could be arrays, but let's keep them scalar and modulate advection instead
    
    # Update
    nextA = A + (Da * lapA - reaction + f * (1.0 - A) + advA)
    nextB = B + (Db * lapB + reaction - (f + k) * B + advB)
    
    A = np.clip(nextA, 0.0, 1.0)
    B = np.clip(nextB, 0.0, 1.0)

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    # Fast forward simulation to get initial interesting state
    print("Pre-simulating...")
    for _ in range(500):
        step()
    print("Pre-simulation complete.")

def draw():
    # 8 substeps per frame for fast evolution
    for _ in range(8):
        step()
    
    # Render
    py5.load_np_pixels()
    
    # Color mapping
    # A goes from ~0.2 to 1.0, B goes from ~0.0 to ~0.3
    # We use B as the primary structural element
    normB = B / (np.max(B) + 1e-5)
    
    # Background: Liquid Obsidian (0, 0, 0)
    # Dominant: Bioluminescent Lime (#39FF14 -> 57, 255, 20)
    # Secondary: Deep Violet (#4B0082 -> 75, 0, 130)
    # Accent: Silver (#C0C0C0 -> 192, 192, 192)
    
    # Map B to these colors
    # 0.0 -> Black
    # 0.3 -> Deep Violet
    # 0.6 -> Bioluminescent Lime
    # 0.9 -> Silver
    
    r = np.zeros_like(B)
    g = np.zeros_like(B)
    b_chan = np.zeros_like(B)
    
    # Mix colors based on thresholds
    mask1 = normB < 0.3
    mask2 = (normB >= 0.3) & (normB < 0.6)
    mask3 = normB >= 0.6
    
    # 0 to 0.3: Black to Violet
    t1 = normB[mask1] / 0.3
    r[mask1] = t1 * 75
    g[mask1] = 0
    b_chan[mask1] = t1 * 130
    
    # 0.3 to 0.6: Violet to Lime
    t2 = (normB[mask2] - 0.3) / 0.3
    r[mask2] = 75 + t2 * (57 - 75)
    g[mask2] = 0 + t2 * (255 - 0)
    b_chan[mask2] = 130 + t2 * (20 - 130)
    
    # 0.6 to 1.0: Lime to Silver
    t3 = (normB[mask3] - 0.6) / 0.4
    r[mask3] = 57 + t3 * (192 - 57)
    g[mask3] = 255 + t3 * (192 - 255)
    b_chan[mask3] = 20 + t3 * (192 - 20)
    
    # Stack to RGBA (sim size)
    pixels = np.zeros((SIM_H, SIM_W, 4), dtype=np.uint8)
    pixels[..., 0] = r.astype(np.uint8) # R
    pixels[..., 1] = g.astype(np.uint8) # G
    pixels[..., 2] = b_chan.astype(np.uint8) # B
    pixels[..., 3] = 255 # A
    
    # Scale up to actual pixel size
    actual_h, actual_w = py5.np_pixels.shape[:2]
    scale_y = actual_h // SIM_H
    scale_x = actual_w // SIM_W
    
    scaled_pixels = np.repeat(np.repeat(pixels, scale_y, axis=0), scale_x, axis=1)
    
    # If scaled_pixels doesn't exactly match actual size due to integer division, slice or pad it
    if scaled_pixels.shape[0] != actual_h or scaled_pixels.shape[1] != actual_w:
        sh, sw = scaled_pixels.shape[:2]
        ch, cw = min(sh, actual_h), min(sw, actual_w)
        py5.np_pixels[:ch, :cw] = scaled_pixels[:ch, :cw]
    else:
        py5.np_pixels[:] = scaled_pixels
        
    py5.update_np_pixels()
    
    # Add subtle scanlines or noise over it for texture
    py5.fill(0, 15)
    for y_line in range(0, SIZE[1], 4):
        py5.rect(0, y_line, SIZE[0], 2)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()
