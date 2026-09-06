from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid size for complex TDGL
W_sim = 480
H_sim = 270

# Physical constants
B_external = 0.15   # Perpendicular external magnetic field
dt = 0.08           # Time step
gl_kappa = 2.0      # Ginzburg-Landau parameter

# Initialize order parameter psi with random complex noise (magnitude ~ 0.8)
psi = (np.random.rand(H_sim, W_sim) + 1j * np.random.rand(H_sim, W_sim) - (0.5 + 0.5j)) * 0.2
psi = psi.astype(np.complex64)

# Precompute vector potential phase links under Landau gauge: A = (0, B*x, 0)
X_coords = np.arange(W_sim, dtype=np.float32)
# Phase shifts along Y coordinates for gauge-covariant derivative
phase_y = np.exp(1j * B_external * X_coords)[np.newaxis, :]
phase_y_conj = np.conj(phase_y)

# Dynamic pinning center positions (orbiting defects that attract vortices)
pin_centers = []
for i in range(5):
    pin_centers.append({
        "radius": random.uniform(40.0, 100.0),
        "speed": random.uniform(0.005, 0.02) * random.choice([-1, 1]),
        "phase": random.uniform(0, 2 * np.pi)
    })

# Color buffer
colored = np.zeros((H_sim, W_sim, 4), dtype=np.uint8)
colored[..., 3] = 255

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def covariant_laplacian(A):
    # Covariant derivative shifts matching external magnetic vector potential
    psi_right = np.roll(A, -1, axis=1)
    psi_left = np.roll(A, 1, axis=1)
    psi_up = np.roll(A, -1, axis=0) * phase_y
    psi_down = np.roll(A, 1, axis=0) * phase_y_conj
    return psi_right + psi_left + psi_up + psi_down - 4.0 * A

def draw():
    global psi
    
    # 1. Update pinning centers
    t = py5.frame_count
    cx, cy = W_sim / 2.0, H_sim / 2.0
    V_pin = np.zeros((H_sim, W_sim), dtype=np.float32)
    
    X_grid, Y_grid = np.meshgrid(np.arange(W_sim), np.arange(H_sim))
    
    for pin in pin_centers:
        theta = pin["phase"] + t * pin["speed"]
        px = cx + pin["radius"] * np.cos(theta)
        py = cy + pin["radius"] * np.sin(theta)
        # Add local Gaussian pinning potential
        dist_sq = (X_grid - px)**2 + (Y_grid - py)**2
        V_pin += np.exp(-dist_sq / 120.0).astype(np.float32) * 0.7
        
    # Limit pinning potential intensity
    V_pin = np.clip(V_pin, 0.0, 0.9)

    # 2. TDGL integration sub-stepping
    for _ in range(3):
        d2_psi = covariant_laplacian(psi)
        mag_sq = np.abs(psi)**2
        # Ginzburg-Landau equation: d_psi/dt = (1 - V_pin) * psi - |psi|^2 * psi + D^2 psi
        dpsi = (1.0 - V_pin) * psi - mag_sq * psi + d2_psi
        psi += dt * dpsi

    # 3. Render Order Parameter magnitude and phase
    psi_mag = np.abs(psi)
    psi_phase = np.angle(psi)  # Phase angle in [-pi, pi]
    
    # Glow logic:
    # Cores are where psi_mag is close to 0 (vortex centers)
    core_mask = np.clip((1.0 - psi_mag) * 2.2, 0.0, 1.0)
    
    # HSL-like domain coloring based on phase angle
    hue_norm = (psi_phase + np.pi) / (2.0 * np.pi) # Map to [0, 1]
    
    # Spectral violet/teal flow
    r_base = (1.0 - core_mask) * (50.0 + 80.0 * np.sin(hue_norm * 2.0 * np.pi))
    g_base = (1.0 - core_mask) * (15.0 + 40.0 * np.cos(hue_norm * 2.0 * np.pi))
    b_base = (1.0 - core_mask) * (140.0 + 90.0 * np.sin(hue_norm * 2.0 * np.pi + 1.0))
    
    # Bright glowing teal vortex cores
    r_core = core_mask * 0.0
    g_core = core_mask * 230.0
    b_core = core_mask * 255.0
    
    # Saffron magnetic halo around cores
    halo = np.clip((1.0 - psi_mag) * (psi_mag * 4.0), 0.0, 1.0)
    r_halo = halo * 255.0
    g_halo = halo * 150.0
    b_halo = halo * 20.0
    
    # Blend base, cores, and halos
    r_out = r_base + r_core + r_halo
    g_out = g_base + g_core + g_halo
    b_out = b_base + b_core + b_halo
    
    colored[..., 0] = np.clip(r_out, 0, 255).astype(np.uint8)
    colored[..., 1] = np.clip(g_out, 0, 255).astype(np.uint8)
    colored[..., 2] = np.clip(b_out, 0, 255).astype(np.uint8)
    
    py5.background(0)
    
    # Display simulation frame
    img = py5.create_image(W_sim, H_sim, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = colored
        img.update_np_pixels()
    else:
        r = colored[..., 0].astype(np.int32)
        g = colored[..., 1].astype(np.int32)
        b = colored[..., 2].astype(np.int32)
        a = colored[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()
        
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save preview snapshot (middle frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
