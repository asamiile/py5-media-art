from pathlib import Path
import math
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid resolution for 4K quantum fluid simulation
GRID_W = 480
GRID_H = 270

# Quantum vortex parameters
N_VORTICES = 37  # Triangular Abrikosov lattice
HEALING_LENGTH = 14.0  # Healing length xi in grid units

# Particle tracers
N_TRACERS = 3000
tracer_pos = None


def generate_abrikosov_lattice(t):
    """
    Generate 37 vortex core locations forming a rotating hexagonal Abrikosov lattice.
    """
    vortices = []
    # Ring 0: Center vortex
    vortices.append((GRID_W / 2.0, GRID_H / 2.0, 1))
    
    # Ring 1: 6 vortices
    r1 = 35.0
    for i in range(6):
        a = i * (math.pi / 3.0) + t * 0.4
        vortices.append((GRID_W / 2.0 + r1 * math.cos(a), GRID_H / 2.0 + r1 * math.sin(a), 1 if i % 2 == 0 else -1))
        
    # Ring 2: 12 vortices
    r2 = 70.0
    for i in range(12):
        a = i * (math.pi / 6.0) - t * 0.25
        vortices.append((GRID_W / 2.0 + r2 * math.cos(a), GRID_H / 2.0 + r2 * math.sin(a), 1 if i % 3 == 0 else -1))
        
    # Ring 3: 18 vortices
    r3 = 105.0
    for i in range(18):
        a = i * (math.pi / 9.0) + t * 0.15
        vortices.append((GRID_W / 2.0 + r3 * math.cos(a), GRID_H / 2.0 + r3 * math.sin(a), 1))
        
    return vortices


def setup():
    global tracer_pos
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particle tracers uniformly
    np.random.seed(42)
    tracer_pos = np.zeros((N_TRACERS, 2), dtype=np.float32)
    tracer_pos[:, 0] = np.random.uniform(0, SIZE[0], N_TRACERS)
    tracer_pos[:, 1] = np.random.uniform(0, SIZE[1], N_TRACERS)


def draw():
    global tracer_pos
    py5.background(2, 6, 18)  # Deep quantum void (#020612)
    
    t = py5.frame_count / 60.0
    w, h = float(SIZE[0]), float(SIZE[1])
    cx, cy = w / 2.0, h / 2.0
    
    # Grid coordinates
    gx = np.linspace(0, GRID_W, GRID_W, dtype=np.float32)
    gy = np.linspace(0, GRID_H, GRID_H, dtype=np.float32)
    X, Y = np.meshgrid(gx, gy)
    
    vortices = generate_abrikosov_lattice(t)
    
    # Compute complex wave function psi = sqrt(density) * exp(i * phase)
    density = np.ones_like(X, dtype=np.float32)
    phase = np.zeros_like(X, dtype=np.float32)
    
    for vx, vy, charge in vortices:
        dx = X - vx
        dy = Y - vy
        r = np.hypot(dx, dy)
        ang = np.arctan2(dy, dx)
        
        # Core suppression tanh(r / xi)
        density *= np.tanh(r / (HEALING_LENGTH / 2.0)) ** 2
        # Phase accumulation
        phase += charge * ang
        
    # Superfluid phonon wave ripple
    r_center = np.hypot(X - GRID_W / 2.0, Y - GRID_H / 2.0)
    phonon_wave = 0.15 * np.sin(r_center * 0.25 - t * 3.0) * np.cos(6.0 * np.arctan2(Y - GRID_H / 2.0, X - GRID_W / 2.0))
    phase += phonon_wave
    
    # Normalize phase to [-pi, pi]
    phase = (phase + np.pi) % (2.0 * np.pi) - np.pi
    
    # Map phase and density to RGB image buffer
    # Spectral palette:
    # Phase -pi..0..pi: Deep Indigo (0, 30, 90) -> Electric Cyan (6, 182, 212) -> Emerald Green (16, 185, 129) -> Solar Gold (250, 204, 21) -> Crimson Violet (225, 29, 72)
    phase_norm = (phase + np.pi) / (2.0 * np.pi)  # 0..1
    
    # Interpolate colors across spectral phase loop
    r_channel = np.clip(120.0 * np.sin(phase_norm * 2 * np.pi) + 135.0, 0, 255)
    g_channel = np.clip(120.0 * np.sin(phase_norm * 2 * np.pi + 2.0 * np.pi / 3.0) + 120.0, 0, 255)
    b_channel = np.clip(120.0 * np.sin(phase_norm * 2 * np.pi + 4.0 * np.pi / 3.0) + 135.0, 0, 255)
    
    # Multiply by density
    r_channel = (r_channel * density).astype(np.uint8)
    g_channel = (g_channel * density).astype(np.uint8)
    b_channel = (b_channel * density).astype(np.uint8)
    
    # Stack into RGB array
    img_array = np.dstack((r_channel, g_channel, b_channel))
    
    # Convert numpy array to py5 image and display scaled to 4K canvas
    img = py5.create_image_from_numpy(img_array, 'RGB')
    py5.image(img, 0, 0, w, h)
    
    # Draw Iso-Phase Contour Streamlines (glowing lines along constant phase angles)
    py5.stroke_weight(1.5)
    scale_x = w / GRID_W
    scale_y = h / GRID_H
    
    # Overlay tracer particles advected along superfluid velocity field
    py5.stroke(255, 255, 255, 180)
    py5.stroke_weight(2.0)
    
    for i in range(N_TRACERS):
        px, py = tracer_pos[i, 0], tracer_pos[i, 1]
        grid_px = px / scale_x
        grid_py = py / scale_y
        
        # Calculate velocity field v_s = grad(phase) from vortices
        vx_total, vy_total = 0.0, 0.0
        for vx, vy, charge in vortices:
            dx = grid_px - vx
            dy = grid_py - vy
            r2 = dx * dx + dy * dy + 1e-4
            # Velocity of point vortex v = charge * (-dy, dx) / r^2
            vx_total += charge * (-dy) / r2
            vy_total += charge * dx / r2
            
        tracer_pos[i, 0] += vx_total * scale_x * 8.0
        tracer_pos[i, 1] += vy_total * scale_y * 8.0
        
        # Wrap around bounds
        if tracer_pos[i, 0] < 0 or tracer_pos[i, 0] >= w or tracer_pos[i, 1] < 0 or tracer_pos[i, 1] >= h:
            tracer_pos[i, 0] = np.random.uniform(0, w)
            tracer_pos[i, 1] = np.random.uniform(0, h)
            
        py5.point(tracer_pos[i, 0], tracer_pos[i, 1])
        
    py5.blend_mode(py5.BLEND)
    
    # Save frame
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
