from pathlib import Path
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
N_PARTICLES = 240_000
VORTEX_RADIUS = 420
VORTEX_STRENGTH = 1800
KELVIN_AMPLITUDE = 60
KELVIN_FREQ = 8
KELVIN_SPEED = 0.12

# State
particles = None
colors = None
vortex_phase = 0


def setup():
    global particles, colors
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize particles in rings
    particles = np.zeros((N_PARTICLES, 3), dtype=np.float32)
    colors = np.zeros((N_PARTICLES, 3), dtype=np.float32)

    particles_per_ring = N_PARTICLES // 3
    
    for i in range(3):
        start = i * particles_per_ring
        end = (i + 1) * particles_per_ring
        
        # Random distribution near rings
        angle = np.random.uniform(0, 2 * np.pi, particles_per_ring)
        r = VORTEX_RADIUS + np.random.normal(0, 25, particles_per_ring)
        
        offset_z = (i - 1) * 180
        
        particles[start:end, 0] = r * np.cos(angle)
        particles[start:end, 1] = r * np.sin(angle)
        particles[start:end, 2] = offset_z + np.random.normal(0, 10, particles_per_ring)
        
        # Color mapping (Electric Ice -> Amethyst -> Cobalt)
        # Hues: 180 (Cyan), 280 (Amethyst), 220 (Cobalt)
        hues = [180, 280, 220]
        hue = np.random.normal(hues[i], 10, particles_per_ring) % 360
        colors[start:end, 0] = hue
        colors[start:end, 1] = 70 + np.random.uniform(0, 30, particles_per_ring)
        colors[start:end, 2] = 80 + np.random.uniform(0, 20, particles_per_ring)


def draw():
    global particles, vortex_phase
    
    py5.background(0)
    
    # Update vortex phase for Kelvin waves
    vortex_phase += KELVIN_SPEED
    
    # 1. Update Simulation
    t = py5.frame_count / FPS
    
    # Center rotation (slower)
    rot_speed = 0.005
    cos_rot = np.cos(rot_speed)
    sin_rot = np.sin(rot_speed)
    
    # Apply rotation to particles
    x = particles[:, 0]
    y = particles[:, 1]
    particles[:, 0] = x * cos_rot - y * sin_rot
    particles[:, 1] = x * sin_rot + y * cos_rot
    
    # Helical Perturbation (Kelvin Waves)
    angle = np.arctan2(particles[:, 1], particles[:, 0])
    
    # Induce vertical "wobble"
    wave = np.sin(angle * KELVIN_FREQ + vortex_phase) * KELVIN_AMPLITUDE
    particles[:, 2] += (wave - particles[:, 2] * 0.05) * 0.1
    
    # 2. Additive Background Stars (Dense)
    py5.stroke_weight(1)
    for _ in range(40):
        sx = np.random.uniform(0, py5.width)
        sy = np.random.uniform(0, py5.height)
        py5.stroke(255, 255, 255, np.random.uniform(10, 60))
        py5.point(sx, sy)

    # 3. Manual 3D to 2D Projection
    # Camera rotation (more dynamic)
    cam_angle_y = t * 0.25
    cam_angle_x = np.sin(t * 0.15) * 0.3
    
    # Rotate Y
    cy, sy = np.cos(cam_angle_y), np.sin(cam_angle_y)
    px1 = particles[:, 0] * cy - particles[:, 2] * sy
    pz1 = particles[:, 0] * sy + particles[:, 2] * cy
    py1 = particles[:, 1]
    
    # Rotate X
    cx, sx = np.cos(cam_angle_x), np.sin(cam_angle_x)
    px = px1
    py = py1 * cx - pz1 * sx
    pz = py1 * sx + pz1 * cx
    
    # Perspective projection
    fov = 1000
    z_offset = 1500
    s = fov / (pz + z_offset)
    
    screen_x = px * s + py5.width / 2
    screen_y = py * s + py5.height / 2
    
    # 4. Render Particles
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    mask = (screen_x > 0) & (screen_x < py5.width) & (screen_y > 0) & (screen_y < py5.height)
    sx_masked = screen_x[mask]
    sy_masked = screen_y[mask]
    c_masked = colors[mask]
    
    # Chunked points for performance
    chunk_size = 8000
    for i in range(0, len(sx_masked), chunk_size):
        end = min(i + chunk_size, len(sx_masked))
        ring_idx = (i // (N_PARTICLES // 3)) % 3
        hues = [180, 280, 220]
        h = hues[ring_idx]
        
        # Glow pass (larger, fainter)
        py5.stroke_weight(3)
        py5.stroke(h, 80, 100, 4)
        py5.points(np.stack([sx_masked[i:end], sy_masked[i:end]], axis=1))
        
        # Core pass (sharper)
        py5.stroke_weight(1.2)
        py5.stroke(h, 60, 100, 15)
        py5.points(np.stack([sx_masked[i:end], sy_masked[i:end]], axis=1))


    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # ffmpeg assembly
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "17", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        # Preview image
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
