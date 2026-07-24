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

# Cymatics Parameters
NUM_PARTICLES = 1000000
STEPS_PER_FRAME = 2
DT = 0.005
FRICTION = 0.85
NOISE = 0.002

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colormap
    
    # Initialize particles randomly in [-1, 1] x [-1, 1]
    pos = np.random.uniform(-1.0, 1.0, (NUM_PARTICLES, 2)).astype(np.float32)
    vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    
    # Pre-generate a Gold/Sand colormap based on particle velocity/energy
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        # Color mapping: Dark Brown -> Gold -> White
        if v < 0.5:
            p = v / 0.5
            colormap[i, 1:] = [int(100 * p), int(50 * p), 0]
        else:
            p = (v - 0.5) / 0.5
            colormap[i, 1:] = [100 + int(155 * p), 50 + int(205 * p), int(255 * p)]

def step_physics(t):
    global pos, vel
    
    # Slowly morph the Chladni parameters N and M over time
    N = 4.0 + 3.0 * np.sin(t * 0.5)
    M = 4.0 + 3.0 * np.cos(t * 0.618)
    
    x = pos[:, 0]
    y = pos[:, 1]
    
    # Chladni Equation Z(x,y)
    npx = N * np.pi * x
    mpy = M * np.pi * y
    mpx = M * np.pi * x
    npy = N * np.pi * y
    
    sin_npx = np.sin(npx)
    sin_mpy = np.sin(mpy)
    sin_mpx = np.sin(mpx)
    sin_npy = np.sin(npy)
    
    cos_npx = np.cos(npx)
    cos_mpy = np.cos(mpy)
    cos_mpx = np.cos(mpx)
    cos_npy = np.cos(npy)
    
    Z = sin_npx * sin_mpy + sin_mpx * sin_npy
    
    # Gradients
    Zx = N * np.pi * cos_npx * sin_mpy + M * np.pi * cos_mpx * sin_npy
    Zy = M * np.pi * sin_npx * cos_mpy + N * np.pi * sin_mpx * cos_npy
    
    # Force = -2 * Z * Gradient(Z)
    fx = -2.0 * Z * Zx
    fy = -2.0 * Z * Zy
    
    # Update velocity with force, friction, and thermal noise
    vel[:, 0] = (vel[:, 0] + fx * DT) * FRICTION + np.random.uniform(-NOISE, NOISE, NUM_PARTICLES)
    vel[:, 1] = (vel[:, 1] + fy * DT) * FRICTION + np.random.uniform(-NOISE, NOISE, NUM_PARTICLES)
    
    # Move particles
    pos += vel * DT
    
    # Bounce off walls [-1, 1]
    hit_x_low = pos[:, 0] < -1.0
    hit_x_high = pos[:, 0] > 1.0
    vel[hit_x_low | hit_x_high, 0] *= -0.5
    pos[:, 0] = np.clip(pos[:, 0], -1.0, 1.0)
    
    hit_y_low = pos[:, 1] < -1.0
    hit_y_high = pos[:, 1] > 1.0
    vel[hit_y_low | hit_y_high, 1] *= -0.5
    pos[:, 1] = np.clip(pos[:, 1], -1.0, 1.0)

def draw():
    global pos, vel
    
    t = py5.frame_count * 0.02
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Fade background slightly to create motion blur trails
    pixels = py5.np_pixels
    pixels[:, :, 1:] = (pixels[:, :, 1:].astype(np.uint16) * 200 // 256).astype(np.uint8)
    
    # Map [-1, 1] to screen coordinates
    W, H = SIZE
    pad = 100
    screen_x = ((pos[:, 0] + 1.0) * 0.5 * (W - pad * 2) + pad).astype(np.int32)
    screen_y = ((pos[:, 1] + 1.0) * 0.5 * (H - pad * 2) + pad).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    # Determine color based on kinetic energy (velocity magnitude)
    v_mag = np.sqrt(vel[valid, 0]**2 + vel[valid, 1]**2)
    color_indices = np.clip(v_mag * 15.0, 0, 255).astype(np.uint8)
    
    # Draw points (Additive blending directly to pixel array)
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    vr = colormap[color_indices, 1]
    vg = colormap[color_indices, 2]
    vb = colormap[color_indices, 3]
    
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
