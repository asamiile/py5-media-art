from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import cv2
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation grid size (lower res for fast stable updates, then upscaled to 4K)
SIM_W = 640
SIM_H = 360

# Quantum wave packet parameters
dt = 0.04  # Time step (stable under Courant limit with V=20)
c = 2.0    # hbar / (2 * m) parameter
gain = 2.5 # Brightness multiplier for probability density

# Initialize wave function: Real (R) and Imaginary (I) parts
R = np.zeros((SIM_H, SIM_W), dtype=np.float32)
I = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Create Potential Barrier V(y, x)
# V = 0 is free space; high values are barriers
V = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# 1. Double-slit barrier in the middle
slit_x = SIM_W // 2 - 40
barrier_width = 12
slit_spacing = 30
slit_height = 14

V[:, slit_x : slit_x + barrier_width] = 20.0  # Solid wall

# Open the two slits
mid_y = SIM_H // 2
V[mid_y - slit_spacing - slit_height : mid_y - slit_spacing + slit_height, slit_x : slit_x + barrier_width] = 0.0
V[mid_y + slit_spacing - slit_height : mid_y + slit_spacing + slit_height, slit_x : slit_x + barrier_width] = 0.0

# 2. Add some circular scatterers on the right side
circles = [
    (SIM_W // 2 + 100, SIM_H // 2 - 60, 20),
    (SIM_W // 2 + 100, SIM_H // 2 + 60, 20),
    (SIM_W // 2 + 180, SIM_H // 2, 28)
]

for cx, cy, r in circles:
    y_grid, x_grid = np.ogrid[:SIM_H, :SIM_W]
    mask = (x_grid - cx)**2 + (y_grid - cy)**2 <= r**2
    V[mask] = 20.0

# Absorbing boundary sponge layer (prevents border reflections)
sponge = np.ones((SIM_H, SIM_W), dtype=np.float32)
thickness = 25
for i in range(thickness):
    factor = 0.95 + 0.05 * (i / thickness)**2
    # Apply to all 4 edges
    sponge[i, :] *= factor
    sponge[-1 - i, :] *= factor
    sponge[:, i] *= factor
    sponge[:, -1 - i] *= factor

# Memory holder for mid-frame preview
img_rgb_mid = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    # Recreate clean frames directory
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize the first wave packet
    spawn_wave_packet(R, I, x0=60, y0=SIM_H // 2, kx=1.2, ky=0.0, sigma=28.0)


def spawn_wave_packet(r_grid, i_grid, x0, y0, kx, ky, sigma):
    """Spawns a new Gaussian wave packet with momentum (kx, ky) into the grid."""
    y_grid, x_grid = np.ogrid[:SIM_H, :SIM_W]
    dist_sq = (x_grid - x0)**2 + (y_grid - y0)**2
    envelope = np.exp(-dist_sq / (4.0 * sigma**2))
    
    phase = kx * x_grid + ky * y_grid
    r_grid += envelope * np.cos(phase)
    i_grid += envelope * np.sin(phase)


def draw():
    global R, I, img_rgb_mid
    
    # 1. Periodically spawn a new wave packet to keep the animation rich and dynamic
    if py5.frame_count == 400:
        # Spawn an interfering second wave packet from the top-left corner
        spawn_wave_packet(R, I, x0=60, y0=60, kx=1.0, ky=0.4, sigma=26.0)
    elif py5.frame_count == 800:
        # Spawn another wave packet from the bottom-left corner
        spawn_wave_packet(R, I, x0=60, y0=SIM_H - 60, kx=1.0, ky=-0.4, sigma=26.0)
        
    # 2. Time-Dependent Schrödinger Equation Solver Step (Leapfrog sub-stepping)
    for _ in range(8):
        # Compute Laplacian via 5-point finite difference scheme
        laplacian_R = (
            np.roll(R, 1, axis=0) + np.roll(R, -1, axis=0) +
            np.roll(R, 1, axis=1) + np.roll(R, -1, axis=1) - 4 * R
        )
        # Imaginary part update: dI/dt = -H R = c * del^2 R - V * R
        I = I + dt * (c * laplacian_R - V * R)
        I *= sponge
        
        # Compute Laplacian of the updated Imaginary part
        laplacian_I = (
            np.roll(I, 1, axis=0) + np.roll(I, -1, axis=0) +
            np.roll(I, 1, axis=1) + np.roll(I, -1, axis=1) - 4 * I
        )
        # Real part update: dR/dt = H I = -c * del^2 I + V * I
        R = R - dt * (c * laplacian_I - V * I)
        R *= sponge
    
    # 3. Render probability density and phase
    prob = R**2 + I**2
    phase = np.arctan2(I, R)
    
    # Convert phase and probability density to HSV
    hsv = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    hsv[:, :, 0] = (phase + np.pi) / (2.0 * np.pi) * 360.0  # Hue in [0, 360]
    hsv[:, :, 1] = 0.9  # Rich saturation
    
    # Map probability to Value (with a non-linear scaling for better tail visibility)
    val = np.clip(np.sqrt(prob) * gain, 0.0, 1.0)
    hsv[:, :, 2] = val
    
    # Convert HSV to RGB
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    # 4. Burn potential barriers into the simulation visualization (in dark grey/blue)
    barrier_mask = V > 0.0
    rgb[barrier_mask] = rgb[barrier_mask] * 0.15 + np.array([0.1, 0.12, 0.18], dtype=np.float32) * 0.85
    
    # 5. Upscale to native 4K resolution
    rgb_full = cv2.resize(rgb, (SIZE[0], SIZE[1]), interpolation=cv2.INTER_LINEAR)
    img_rgb = (np.clip(rgb_full, 0.0, 1.0) * 255.0).astype(np.uint8)
    
    # Save mid-frame preview
    if py5.frame_count == TOTAL_FRAMES // 2:
        img_rgb_mid = img_rgb.copy()
        
    # Write to screen
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = img_rgb[:, :, 0]
    py5.np_pixels[:, :, 1] = img_rgb[:, :, 1]
    py5.np_pixels[:, :, 2] = img_rgb[:, :, 2]
    py5.np_pixels[:, :, 3] = 255
    py5.update_np_pixels()
    
    # 6. Render Native 4K HUD Overlay on top
    # Telemetry text
    py5.no_stroke()
    py5.fill(255, 255, 255, 200)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text(f"QUANTUM WAVE-PACKET SIMULATOR // 2D TDSE FDTD", 50, 50)
    py5.text(f"GRID RESOLUTION: {SIM_W}x{SIM_H} (UPSCALED TO 4K)", 50, 85)
    py5.text(f"WAVE FUNCTION: psi(x,y,t) = R + iI", 50, 120)
    py5.text(f"TIMESTEP dt: {dt:.3f} | PARAMS: c={c:.2f}, gain={gain:.1f}", 50, 155)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"ABSORBING SPONGE LAYER BOUNDARY: ACTIVE", SIZE[0] - 50, 85)
    
    # Draw nice thin vector borders for the potential barriers at 4K resolution
    py5.stroke(255, 200, 50, 180)  # Golden borders
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Draw double-slit wall border
    scale_y = SIZE[1] / SIM_H
    scale_x = SIZE[0] / SIM_W
    
    wall_left = slit_x * scale_x
    wall_right = (slit_x + barrier_width) * scale_x
    
    # Draw upper section of slit wall
    py5.rect(wall_left, 0, wall_right - wall_left, (mid_y - slit_spacing - slit_height) * scale_y)
    # Draw middle section of slit wall
    py5.rect(wall_left, (mid_y - slit_spacing + slit_height) * scale_y, wall_right - wall_left, (slit_spacing * 2 - slit_height * 2) * scale_y)
    # Draw bottom section of slit wall
    py5.rect(wall_left, (mid_y + slit_spacing + slit_height) * scale_y, wall_right - wall_left, SIZE[1] - (mid_y + slit_spacing + slit_height) * scale_y)
    
    # Draw circular pillars
    for cx, cy, r in circles:
        py5.ellipse(cx * scale_x, cy * scale_y, r * 2 * scale_x, r * 2 * scale_y)
        
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
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
        
        # Save preview snapshot
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
