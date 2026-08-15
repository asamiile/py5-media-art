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

# Simulation Grid (160x90 for fast physical integration, upscaled to 4K for aesthetics)
GRID_W = 192
GRID_H = 108

# Physical parameters
dx = 0.5
dy = 0.5
dt = 0.1
c_sq = 1.0     # Wave propagation speed squared
damping = 0.015 # Global dissipation to stabilize the system and add fluidic trails

# Field buffers
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
u_prev = np.zeros((GRID_H, GRID_W), dtype=np.float32)
energy_history = []

def init_breather(x0, y0, kx, ky, freq, size, amp):
    """
    Initializes a dynamic breather soliton wave packet.
    """
    global u, u_prev
    y_idx, x_idx = np.indices((GRID_H, GRID_W), dtype=np.float32)
    
    # Distance from center
    dist = np.sqrt((x_idx - x0)**2 + (y_idx - y0)**2)
    
    # Breather profile approximation: spatial envelope * temporal modulation
    envelope = amp * np.exp(- (dist / size)**2)
    
    # Apply initial phase velocity and spatial modulation
    u += envelope * np.cos(0.0)
    # Estimate previous state for leapfrog integration to create momentum
    phase_offset = (x_idx * kx + y_idx * ky)
    u_prev += envelope * np.cos(-dt * freq + phase_offset)

# Set up initial solitons traveling towards each other
# Soliton 1: Left-center, moving right-down
init_breather(GRID_W * 0.3, GRID_H * 0.4, 0.2, 0.05, 0.4, 12.0, 4.5)
# Soliton 2: Right-center, moving left-up
init_breather(GRID_W * 0.7, GRID_H * 0.6, -0.2, -0.05, 0.4, 12.0, 4.5)

def update_physics():
    """
    Solves Sine-Gordon equation using finite difference leapfrog integration.
    u_next = 2*u - u_prev + dt^2 * (c^2 * Laplacian(u) - sin(u) - damping * (u - u_prev)/dt)
    """
    global u, u_prev
    
    # Laplacian using 5-point stencil with periodic wrapping
    u_left = np.roll(u, 1, axis=1)
    u_right = np.roll(u, -1, axis=1)
    u_up = np.roll(u, 1, axis=0)
    u_down = np.roll(u, -1, axis=0)
    
    laplacian = (u_left + u_right + u_up + u_down - 4.0 * u) / (dx * dy)
    
    # Velocity approximation for damping
    vel = (u - u_prev) / dt
    
    # Sine-Gordon step
    u_next = 2.0 * u - u_prev + (dt**2) * (c_sq * laplacian - np.sin(u) - damping * vel)
    
    # Update buffers
    u_prev[:] = u
    u[:] = u_next
    
    # Calculate Hamiltonian energy density field
    # E = 0.5 * (u_t)^2 + 0.5 * c^2 * (grad u)^2 + (1 - cos u)
    grad_u_x = (u_right - u_left) / (2.0 * dx)
    grad_u_y = (u_down - u_up) / (2.0 * dy)
    energy_density = 0.5 * (vel**2) + 0.5 * c_sq * (grad_u_x**2 + grad_u_y**2) + (1.0 - np.cos(u))
    
    return energy_density

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(2, 2, 8)

def draw():
    # --- 1. Physics Step ---
    energy = update_physics()
    
    # Calculate total energy telemetry
    total_energy = np.sum(energy)
    energy_history.append(total_energy)
    if len(energy_history) > 300:
        energy_history.pop(0)
        
    # --- 2. Render Screen ---
    py5.blend_mode(py5.BLEND)
    # Translucent backdrop trails to capture glowing soliton trails
    py5.fill(2, 2, 8, 12)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scaling to 4K viewport
    py5.push_matrix()
    py5.scale(SIZE[0] / GRID_W, SIZE[1] / GRID_H)
    
    # Additive blend mode for the bioluminescent glow
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Upscale energy density field for smooth contours
    energy_upscaled = cv2.resize(energy, (960, 540), interpolation=cv2.INTER_CUBIC)
    
    # Extract contour isolines of energy density
    # Breather cores have high energy density, tails have lower
    levels = [0.08, 0.15, 0.25, 0.40, 0.65, 1.00, 1.50, 2.20, 3.20, 4.50]
    
    scale_c_x = GRID_W / 960.0
    scale_c_y = GRID_H / 540.0
    
    for idx, lvl in enumerate(levels):
        mask = (energy_upscaled >= lvl).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Color sweep: Amethyst Violet (280) to Electric Rose (330) to Saffron Gold (45)
        if idx < 4:
            h = 280.0 + idx * 5.0 # Muted Violet outer rings
            s = 85.0
            b = 40.0 + idx * 5.0
        elif idx < 8:
            h = 300.0 + (idx - 4) * 10.0 # Hot pink/rose mid rings
            s = 90.0
            b = 60.0 + (idx - 4) * 8.0
        else:
            h = 340.0 + (idx - 8) * 32.0 # Saffron gold core
            if h >= 360.0:
                h -= 360.0
            s = 80.0 + (idx - 8) * 5.0
            b = 90.0 + (idx - 8) * 5.0
            
        py5.stroke(h, s, b, 110)
        py5.stroke_weight(1.0 + idx * 0.3)
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
    
    # Text headers
    py5.fill(255, 255, 255, 170)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("SINE-GORDON BREATHER SOLITON INTERFEROMETER", 50, 50)
    py5.text("2D FINITE DIFFERENCE WAVE FIELD DYNAMICS", 50, 85)
    
    py5.text_size(16)
    py5.text(f"SIMULATION SPACE: {GRID_W} x {GRID_H} GRID", 50, 130)
    py5.text(f"INTEGRATION STEP (dt): {dt:.2f} | VELOCITY CAP (c): {c_sq:.1f}", 50, 155)
    py5.text(f"CONTOUR RESOLUTION: {len(levels)} POTENTIAL PHASES", 50, 180)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text_size(24)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text_size(16)
    py5.text(f"SYSTEM DISSIPATION FACTOR: {damping:.4f}", SIZE[0] - 50, 85)
    py5.text(f"TOTAL HAMILTONIAN ENERGY: {total_energy:.2f} eV", SIZE[0] - 50, 110)
    
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
    py5.text("HAMILTONIAN ENERGY WAVEFORM", gx + 8, gy + 8)
    
    # Draw energy wave graph
    py5.no_fill()
    py5.stroke(247, 37, 133, 200) # Hot pink stroke
    py5.stroke_weight(2.0)
    py5.begin_shape()
    max_val = max(energy_history) if len(energy_history) > 0 else 1.0
    min_val = min(energy_history) if len(energy_history) > 0 else 0.0
    val_range = max_val - min_val if max_val != min_val else 1.0
    
    for idx, val in enumerate(energy_history):
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
