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

# Quantum Orbital Parameters
NUM_PARTICLES = 1500000
BOX_SIZE = 18.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, r, theta, phi
    
    # Generate particles with a probability distribution biased towards the center
    # using a Gaussian distribution, so we don't waste particles in empty space
    pos = np.random.normal(0, BOX_SIZE / 3.0, (NUM_PARTICLES, 3)).astype(np.float32)
    
    # Calculate spherical coordinates (r, theta, phi)
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]
    
    r = np.sqrt(x**2 + y**2 + z**2) + 1e-5
    theta = np.arccos(z / r)
    phi = np.arctan2(y, x)
    
    # We also pre-calculate the probability density of our sampling distribution
    # so we can normalize the rendered intensity (Importance Sampling weight)
    global sampling_weight
    # Gaussian PDF: exp(-r^2 / (2 * sigma^2))
    sigma = BOX_SIZE / 3.0
    sampling_weight = np.exp((r**2) / (2.0 * sigma**2))

def get_wavefunctions():
    global r, theta, phi
    
    # Scale factor for Bohr radius
    a0 = 1.2 
    r_scaled = r / a0
    
    # 3d_z^2 orbital (n=3, l=2, m=0)
    R32 = (4.0 / (81.0 * np.sqrt(30.0))) * (r_scaled**2) * np.exp(-r_scaled / 3.0)
    Y20 = np.sqrt(5.0 / (16.0 * np.pi)) * (3.0 * np.cos(theta)**2 - 1.0)
    psi1 = R32 * Y20 * 150.0 # Scaling up for visual brightness
    
    # 3d_x^2-y^2 orbital (n=3, l=2, m=2)
    Y22 = np.sqrt(15.0 / (32.0 * np.pi)) * (np.sin(theta)**2) * np.cos(2.0 * phi)
    psi2 = R32 * Y22 * 150.0
    
    # 4f_x(x^2-3y^2) orbital (n=4, l=3, m=3)
    R43 = (1.0 / (768.0 * np.sqrt(35.0))) * (r_scaled**3) * np.exp(-r_scaled / 4.0)
    Y33 = np.sqrt(35.0 / (64.0 * np.pi)) * (np.sin(theta)**3) * np.cos(3.0 * phi)
    psi3 = R43 * Y33 * 4000.0
    
    return psi1, psi2, psi3

def draw():
    global pos
    
    # Calculate current wavefunction interpolation weights
    t = py5.frame_count * 0.05
    w1 = (np.sin(t * 0.5) + 1.0) * 0.5
    w2 = (np.sin(t * 0.7 + 2.0) + 1.0) * 0.5
    w3 = (np.sin(t * 0.4 + 4.0) + 1.0) * 0.5
    
    # Normalize weights so they sum to 1
    total_w = w1 + w2 + w3
    w1 /= total_w; w2 /= total_w; w3 /= total_w
    
    psi1, psi2, psi3 = get_wavefunctions()
    
    # Superposition of states
    psi = w1 * psi1 + w2 * psi2 + w3 * psi3
    
    # Probability density
    density = psi**2
    
    # Importance sampling normalization: 
    # Because there are more particles at the center, we divide by the sampling probability
    # to get the true visual density.
    intensity = density * sampling_weight * 0.5
    
    py5.load_np_pixels()
    
    # Clear screen (deep space black)
    pixels = py5.np_pixels
    pixels[:, :, 1:] = 0
    
    W, H = SIZE
    
    # 3D Camera Rotation
    cam_angle = t * 0.1
    cos_c, sin_c = np.cos(cam_angle), np.sin(cam_angle)
    
    rot_x = pos[:, 0] * cos_c - pos[:, 2] * sin_c
    rot_y = pos[:, 1]
    rot_z = pos[:, 0] * sin_c + pos[:, 2] * cos_c
    
    # Tilt
    tilt = 0.4
    cos_t, sin_t = np.cos(tilt), np.sin(tilt)
    rot_y2 = rot_y * cos_t - rot_z * sin_t
    rot_z2 = rot_y * sin_t + rot_z * cos_t
    
    # Perspective projection
    fov = H * 1.5
    z_offset = 35.0
    Z = rot_z2 + z_offset
    Z = np.where(Z < 1.0, 1.0, Z)
    
    screen_x = (rot_x * (fov / Z) + W / 2).astype(np.int32)
    screen_y = (rot_y2 * (fov / Z) + H / 2).astype(np.int32)
    
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H) & (intensity > 0.5)
    sx = screen_x[valid]
    sy = screen_y[valid]
    
    valid_intensity = intensity[valid]
    valid_psi = psi[valid]
    
    # The phase of the wavefunction (positive or negative) determines the color
    # Positive -> Cyan/Blue
    # Negative -> Red/Orange
    is_positive = valid_psi > 0
    
    color_r = np.zeros(len(sx), dtype=np.uint16)
    color_g = np.zeros(len(sx), dtype=np.uint16)
    color_b = np.zeros(len(sx), dtype=np.uint16)
    
    # Base intensity mapped to 0-255
    v = np.clip(valid_intensity, 0, 255).astype(np.uint16)
    
    # Positive phase (Cyan/Blue)
    color_r[is_positive] = v[is_positive] // 4
    color_g[is_positive] = v[is_positive]
    color_b[is_positive] = v[is_positive]
    
    # Negative phase (Red/Orange)
    color_r[~is_positive] = v[~is_positive]
    color_g[~is_positive] = v[~is_positive] // 2
    color_b[~is_positive] = v[~is_positive] // 4
    
    # Depth fading (far away = dim)
    depth_fade = np.clip((50.0 - Z[valid]) / 30.0, 0.1, 1.0)
    
    vr = (color_r * depth_fade).astype(np.uint8)
    vg = (color_g * depth_fade).astype(np.uint8)
    vb = (color_b * depth_fade).astype(np.uint8)
    
    flat_indices = sy * W + sx
    flat_pixels = pixels.reshape(-1, 4)
    
    # Additive blend
    # NumPy's add.at handles multiple particles hitting the same pixel correctly
    np.add.at(flat_pixels[:, 1], flat_indices, vr)
    np.add.at(flat_pixels[:, 2], flat_indices, vg)
    np.add.at(flat_pixels[:, 3], flat_indices, vb)
    
    # Clamp to 255
    flat_pixels[:, 1:] = np.clip(flat_pixels[:, 1:], 0, 255)
    
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
