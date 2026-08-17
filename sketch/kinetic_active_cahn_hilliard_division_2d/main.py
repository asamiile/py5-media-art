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

# Grid sizes for physics integration (160x90)
GRID_W = 160
GRID_H = 90

# Cahn-Hilliard active division model parameters
# phi: order parameter (-1 to +1, representing phases)
# mu: chemical potential
# S: active chemical reaction source term representing production/consumption
dx = 1.0
dy = 1.0
dt = 0.04
kappa = 1.0    # Interface gradient energy penalty
mobility = 0.5 # Phase diffusion mobility
gamma = 0.015  # Reaction rate forcing domain size limits (active division pressure)

# Field buffers
phi = np.random.uniform(-0.1, 0.1, (GRID_H, GRID_W)).astype(np.float32)
division_history = []

def update_physics():
    global phi
    
    # Stencil operations for Laplacian (periodic wrapping)
    phi_left = np.roll(phi, 1, axis=1)
    phi_right = np.roll(phi, -1, axis=1)
    phi_up = np.roll(phi, 1, axis=0)
    phi_down = np.roll(phi, -1, axis=0)
    laplacian_phi = (phi_left + phi_right + phi_up + phi_down - 4.0 * phi) / (dx * dy)
    
    # Bulk chemical potential derivative: dF/dphi = phi^3 - phi
    df_dphi = phi**3 - phi
    
    # Chemical potential: mu = df_dphi - kappa * laplacian(phi)
    mu = df_dphi - kappa * laplacian_phi
    
    # Laplacian of chemical potential
    mu_left = np.roll(mu, 1, axis=1)
    mu_right = np.roll(mu, -1, axis=1)
    mu_up = np.roll(mu, 1, axis=0)
    mu_down = np.roll(mu, -1, axis=0)
    laplacian_mu = (mu_left + mu_right + mu_up + mu_down - 4.0 * mu) / (dx * dy)
    
    # Source term representing active production/consumption of phases
    # Forces division when domain sizes exceed the characteristic scale
    source = -gamma * phi
    
    # Cahn-Hilliard update
    phi_next = phi + dt * (mobility * laplacian_mu + source)
    
    # Bound phase field
    phi = np.clip(phi_next, -1.2, 1.2)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(4, 4, 12)

def draw():
    # Perform multiple integration sub-steps for stability
    for _ in range(5):
        update_physics()
        
    # Calculate droplet interface area telemetry
    grad_x = np.roll(phi, -1, axis=1) - np.roll(phi, 1, axis=1)
    grad_y = np.roll(phi, -1, axis=0) - np.roll(phi, 1, axis=0)
    interface_len = np.sum(np.sqrt(grad_x**2 + grad_y**2))
    division_history.append(interface_len)
    if len(division_history) > 300:
        division_history.pop(0)
        
    # --- 2. Render View ---
    py5.blend_mode(py5.BLEND)
    # Slow fading background rect (motion trails)
    py5.fill(4, 4, 12, 16)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.push_matrix()
    py5.scale(SIZE[0] / GRID_W, SIZE[1] / GRID_H)
    
    # Additive neon glow
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Upscale phase field using bicubic interpolation for smooth outlines
    phi_upscaled = cv2.resize(phi, (960, 540), interpolation=cv2.INTER_CUBIC)
    
    # Extract droplet boundaries (interfaces where phi crosses 0)
    levels = [-0.6, -0.3, 0.0, 0.3, 0.6]
    scale_c_x = GRID_W / 960.0
    scale_c_y = GRID_H / 540.0
    
    for idx, lvl in enumerate(levels):
        mask = (phi_upscaled >= lvl).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Color sweep: Amethyst Violet (290) mid levels, Saffron Orange (40) core interface, Turquoise (175) outer shells
        if lvl < 0.0:
            h = 290.0 + lvl * 20.0 # Amethyst tails
            s = 80.0
            b = 45.0 + idx * 5.0
        elif lvl == 0.0:
            h = 40.0 # Saffron dividing interfaces
            s = 95.0
            b = 85.0
        else:
            h = 175.0 - lvl * 20.0 # Turquoise active droplets
            s = 90.0
            b = 60.0 + idx * 5.0
            
        py5.stroke(h, s, b, 120)
        py5.stroke_weight(1.0 + idx * 0.5)
        py5.no_fill()
        
        for c in contours:
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
    py5.text("ACTIVE CAHN-HILLIARD DIVISION MONITOR", 50, 50)
    py5.text("THERMODYNAMIC PHASE-FIELD BIOMECHANICS", 50, 85)
    
    py5.text_size(16)
    py5.text(f"INTEGRATION SCALE: dt={dt:.3f} | kappa={kappa:.1f}", 50, 130)
    py5.text(f"MOBILITY COEFFICIENT: {mobility:.2f}", 50, 155)
    py5.text(f"ACTIVE REACTION TERM (gamma): {gamma:.4f}", 50, 180)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text_size(24)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text_size(16)
    py5.text(f"INTERFACE COMPACTNESS SCORE: {interface_len:.2f} px", SIZE[0] - 50, 85)
    
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
    py5.text("INTERFACE AREA EVOLUTION", gx + 8, gy + 8)
    
    # Draw interface wave graph
    py5.no_fill()
    py5.stroke(40, 200, 180, 200) # Turquoise stroke
    py5.stroke_weight(2.0)
    py5.begin_shape()
    max_val = max(division_history) if len(division_history) > 0 else 1.0
    min_val = min(division_history) if len(division_history) > 0 else 0.0
    val_range = max_val - min_val if max_val != min_val else 1.0
    
    for idx, val in enumerate(division_history):
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
