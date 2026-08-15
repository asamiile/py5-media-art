from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5
import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Grid coordinates (160x90) for fast mathematical updates, upscaled to 4K
GRID_W = 160
GRID_H = 90

# Barkley excitable media parameters
# u: activator, v: inhibitor
# du/dt = 1/eps * u*(1-u)*(u - (v+b)/a) + D * laplacian(u)
# dv/dt = u - v
a = 0.75
b = 0.02
eps = 0.02
D = 0.22       # Diffusion coefficient
dt = 0.003     # Small integration step

# Buffers
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
v = np.zeros((GRID_H, GRID_W), dtype=np.float32)
excitation_history = []

# Seed asymmetric conditions to generate stable spirals
# Let's seed a diagonal split
y_idx, x_idx = np.indices((GRID_H, GRID_W), dtype=np.float32)
u[y_idx > GRID_H / 2] = 1.0
v[x_idx < GRID_W / 2] = 0.3

# Add some perturbation to kickstart chaotic boundaries
u += np.random.rand(GRID_H, GRID_W) * 0.1
u = np.clip(u, 0.0, 1.0)

def update_physics():
    global u, v
    
    # Laplacian using 5-point stencil with periodic wrapping
    u_left = np.roll(u, 1, axis=1)
    u_right = np.roll(u, -1, axis=1)
    u_up = np.roll(u, 1, axis=0)
    u_down = np.roll(u, -1, axis=0)
    laplacian_u = (u_left + u_right + u_up + u_down - 4.0 * u)
    
    # Local reaction terms
    # Avoid divide-by-zero by clamping denominator
    u_th = (v + b) / a
    reaction_u = (1.0 / eps) * u * (1.0 - u) * (u - u_th)
    reaction_v = u - v
    
    # Update u and v using Euler integration
    u_next = u + dt * (reaction_u + D * laplacian_u)
    v_next = v + dt * reaction_v
    
    # Clip states to physical ranges
    u = np.clip(u_next, 0.0, 1.0)
    v = np.clip(v_next, 0.0, 1.0)
    
    # Apply slow advection drift based on Perlin noise-like velocity fields
    # Generate coordinates mapping
    t = py5.frame_count * 0.008
    vel_x = np.sin(x_idx * 0.05 + t) * 0.15
    vel_y = np.cos(y_idx * 0.05 + t) * 0.15
    
    # Grid warping
    map_x = (x_idx + vel_x).astype(np.float32)
    map_y = (y_idx + vel_y).astype(np.float32)
    
    # Apply remap using OpenCV for sub-pixel advection
    u = cv2.remap(u, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    v = cv2.remap(v, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    # Periodically inject localized stimulus to simulate ongoing system noise
    if py5.frame_count % 180 == 0:
        cx, cy = random.randint(20, GRID_W-20), random.randint(20, GRID_H-20)
        dist = np.sqrt((x_idx - cx)**2 + (y_idx - cy)**2)
        u[dist < 6.0] = 1.0
        v[dist < 6.0] = 0.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(8, 12, 18)

def draw():
    # Run multiple physics updates per frame for sub-stepping stability
    for _ in range(8):
        update_physics()
        
    # Calculate global excitation level for HUD
    global_excitation = np.mean(u)
    excitation_history.append(global_excitation)
    if len(excitation_history) > 300:
        excitation_history.pop(0)
        
    # --- 2. Render Screen ---
    py5.blend_mode(py5.BLEND)
    # Slow fading background rect (motion trails)
    py5.fill(8, 12, 18, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.push_matrix()
    py5.scale(SIZE[0] / GRID_W, SIZE[1] / GRID_H)
    
    # Additive neon glow
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Upscale activator field using cubic filtering for smooth contours
    u_upscaled = cv2.resize(u, (960, 540), interpolation=cv2.INTER_CUBIC)
    v_upscaled = cv2.resize(v, (960, 540), interpolation=cv2.INTER_CUBIC)
    
    # Extract propagating excitation fronts (levels of u)
    levels = [0.10, 0.22, 0.38, 0.55, 0.72, 0.88]
    scale_c_x = GRID_W / 960.0
    scale_c_y = GRID_H / 540.0
    
    for idx, lvl in enumerate(levels):
        mask = (u_upscaled >= lvl).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Color mapping: mapping concentration levels to HSB hues
        # Activator maps to Cyan (190) and Emerald (150)
        # Slower inhibitor cores map to Warm Amber (35)
        h = 190.0 - (idx / len(levels)) * 40.0
        s = 85.0
        b = 50.0 + (idx / len(levels)) * 30.0
        
        py5.stroke(h, s, b, 95)
        py5.stroke_weight(1.0 + idx * 0.4)
        py5.no_fill()
        
        for c in contours:
            py5.begin_shape()
            for pt in c:
                px, py = pt[0]
                py5.vertex(px * scale_c_x, py * scale_c_y)
            py5.end_shape(py5.CLOSE)
            
    # Draw local hot spots where inhibitor lags (u high, v low)
    lags = (u_upscaled > 0.85) & (v_upscaled < 0.3)
    if np.any(lags):
        mask_lag = (lags.astype(np.uint8)) * 255
        contours_lag, _ = cv2.findContours(mask_lag, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        py5.stroke(35.0, 95.0, 95.0, 150) # Amber sparks
        py5.stroke_weight(2.5)
        for c in contours_lag:
            py5.begin_shape()
            for pt in c:
                px, py = pt[0]
                py5.vertex(px * scale_c_x, py * scale_c_y)
            py5.end_shape(py5.CLOSE)
            
    py5.pop_matrix()
    
    # --- 3. Telemetry HUD ---
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    py5.fill(255, 255, 255, 170)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("BARKLEY EXCitable wave INTERFEROMETER", 50, 50)
    py5.text("2D ACTIVE REACTION-DIFFUSION NETWORKS", 50, 85)
    
    py5.text_size(16)
    py5.text(f"INTEGRATION SOLVER: dt={dt:.5f} | D={D:.2f}", 50, 130)
    py5.text(f"REACTION THRESHOLD (eps): {eps:.4f}", 50, 155)
    py5.text(f"COEFFICIENTS (a, b): {a:.2f}, {b:.2f}", 50, 180)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text_size(24)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text_size(16)
    py5.text(f"GLOBAL DENSITY INDEX: {global_excitation:.4f}", SIZE[0] - 50, 85)
    
    # Graph Box
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 145
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(13)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("ACTIVATOR FLUX PROFILE", gx + 8, gy + 8)
    
    # Draw energy wave graph
    py5.no_fill()
    py5.stroke(190, 85, 70, 200) # Cyan stroke
    py5.stroke_weight(2.0)
    py5.begin_shape()
    max_val = max(excitation_history) if len(excitation_history) > 0 else 1.0
    min_val = min(excitation_history) if len(excitation_history) > 0 else 0.0
    val_range = max_val - min_val if max_val != min_val else 1.0
    
    for idx, val in enumerate(excitation_history):
        xx = gx + idx * (graph_w / 300.0)
        yy = gy + graph_h - ((val - min_val) / val_range) * (graph_h - 24) - 8
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Blank screen check
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
        
        # Save mid-frame preview
        mid_idx = TOTAL_FRAMES // 2
        mid_file = FRAMES_DIR / f"frame-{mid_idx:04d}.png"
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        shutil.copyfile(mid_file, preview_path)
        print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
        
        # Compile MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Cleanup
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
