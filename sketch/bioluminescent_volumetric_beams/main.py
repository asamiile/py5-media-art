from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import math
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10  # 10 seconds of animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle system state
N_PARTICLES = 1200
particles_x = np.zeros(N_PARTICLES, dtype=np.float32)
particles_y = np.zeros(N_PARTICLES, dtype=np.float32)
particles_vx = np.zeros(N_PARTICLES, dtype=np.float32)
particles_vy = np.zeros(N_PARTICLES, dtype=np.float32)
particles_rad = np.zeros(N_PARTICLES, dtype=np.float32)
particles_phase = np.zeros(N_PARTICLES, dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles
    global particles_x, particles_y, particles_vx, particles_vy, particles_rad, particles_phase
    np.random.seed(137)  # Fix internal seed for reproducibility in particle initialization
    
    particles_x = np.random.uniform(0, SIZE[0], N_PARTICLES).astype(np.float32)
    particles_y = np.random.uniform(0, SIZE[1], N_PARTICLES).astype(np.float32)
    
    # Soft drift velocities
    particles_vx = np.random.uniform(-0.5, 0.5, N_PARTICLES).astype(np.float32)
    particles_vy = np.random.uniform(-0.8, -0.1, N_PARTICLES).astype(np.float32)  # Tendency to float upwards
    
    # Random sizes: most are small dust, a few are larger glowing spores
    particles_rad = np.random.exponential(4.0, N_PARTICLES).astype(np.float32)
    particles_rad = np.clip(particles_rad, 2.0, 24.0)
    
    # Random phases for individual organic breathing
    particles_phase = np.random.uniform(0, 2 * np.pi, N_PARTICLES).astype(np.float32)

def draw():
    # Subtle dark background clear with transparency to create short motion trails
    # Since we want to clear the background but leave a trailing effect,
    # we draw a full-screen semi-transparent rectangle.
    py5.blend_mode(py5.BLEND)
    py5.fill(210, 50, 6, 15)  # Very dark slate/navy with low opacity
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Enable additive blending for glowing light shafts and particles
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # Define light beams: (origin_x, origin_y, base_angle, current_angle, spread_cone, hue, intensity)
    beams = [
        # Beam 1: Top-left swinging sweep (Cyan)
        ((SIZE[0] * 0.1, -100), 0.5 + math.sin(t * 0.7) * 0.25, 0.18, 195, 1.0),
        # Beam 2: Top-right swinging sweep (Seafoam)
        ((SIZE[0] * 0.9, -100), 2.64 + math.sin(t * 0.5 + 1.2) * 0.22, 0.15, 155, 0.95),
        # Beam 3: Bottom-center shining upwards (Lavender)
        ((SIZE[0] * 0.5, SIZE[1] + 100), -math.pi/2 + math.cos(t * 0.4) * 0.2, 0.22, 275, 0.8),
        # Beam 4: Top-center slow spotlight (Gold/Amber)
        ((SIZE[0] * 0.45, -100), math.pi/2 - 0.2 + math.sin(t * 0.6 + 2.0) * 0.15, 0.12, 45, 0.85)
    ]
    
    # Draw volumetric light beams as detailed lines modulated by noise
    for origin, angle, spread, hue, intensity in beams:
        ox, oy = origin
        n_lines = 80
        for j in range(n_lines):
            frac = j / (n_lines - 1)
            line_angle = angle + (frac - 0.5) * 2.0 * spread
            
            # Continuous Perlin noise to simulate turbulent fog/water density variations
            n_val = py5.noise(line_angle * 8.0, t * 1.5)
            
            # Opacity envelope: peaks at center of cone and falls off smoothly to edges
            center_factor = math.cos((frac - 0.5) * math.pi)
            
            alpha = (center_factor ** 3) * n_val * 12.0 * intensity
            
            # Draw line extending past screen limits
            length = 3200
            lx = ox + math.cos(line_angle) * length
            ly = oy + math.sin(line_angle) * length
            
            py5.stroke(hue, 70, 100, alpha)
            py5.stroke_weight(3)
            py5.line(ox, oy, lx, ly)
            
    # Update and render particles using vectorized NumPy math for performance
    global particles_x, particles_y
    
    # Add fluid drift/wiggle based on simple trigonometry and noise
    noise_field_x = np.sin(particles_y * 0.003 + t * 2.0) * 0.6
    noise_field_y = np.cos(particles_x * 0.003 + t * 1.8) * 0.4
    
    particles_x += (particles_vx + noise_field_x)
    particles_y += (particles_vy + noise_field_y)
    
    # Wrap particles around borders
    particles_x = np.mod(particles_x, SIZE[0])
    particles_y = np.mod(particles_y, SIZE[1])
    
    # Vectorized light intersection checks
    best_intensity = np.zeros(N_PARTICLES, dtype=np.float32)
    best_hue = np.full(N_PARTICLES, 195.0, dtype=np.float32)
    
    px = particles_x
    py = particles_y
    
    for origin, angle, spread, hue, intensity in beams:
        ox, oy = origin
        dx = px - ox
        dy = py - oy
        dist = np.sqrt(dx * dx + dy * dy)
        dist = np.maximum(dist, 1.0)
        
        theta_p = np.arctan2(dy, dx)
        
        # Angular difference wrapped to [-pi, pi]
        delta = theta_p - angle
        delta = np.mod(delta + np.pi, 2 * np.pi) - np.pi
        abs_delta = np.abs(delta)
        
        inside = abs_delta < spread
        
        # Quadratic intensity falloff inside the cone, linear distance decay
        cone_factor = np.clip(1.0 - abs_delta / spread, 0.0, 1.0) ** 2.5
        dist_factor = 1.0 / (1.0 + dist * 0.0006)
        
        current_intensity = cone_factor * dist_factor * inside * intensity
        
        # Take the maximum light intensity for each particle
        better = current_intensity > best_intensity
        best_intensity = np.where(better, current_intensity, best_intensity)
        best_hue = np.where(better, hue, best_hue)

    # Convert arrays to CPU loops or py5 draw operations
    # To keep performance optimal, we loop over particles in Python but use fast operations
    # We draw glowing particles based on their light intersection
    py5.no_stroke()
    for i in range(N_PARTICLES):
        rad = particles_rad[i]
        x, y = particles_x[i], particles_y[i]
        intensity = best_intensity[i]
        hue = best_hue[i]
        
        # Individual particle breathing
        breath = 0.8 + 0.2 * math.sin(t * 3.0 + particles_phase[i])
        
        # Draw particle
        if intensity > 0.01:
            # Illuminated spore: glows in the color of the intersecting light beam
            alpha = (10 + intensity * 85) * breath
            py5.fill(hue, 55, 100, alpha)
            py5.circle(x, y, rad * (1.0 + intensity * 0.6))
            
            # Subtle core glow
            py5.fill(hue, 15, 100, alpha * 0.6)
            py5.circle(x, y, rad * 0.4)
        else:
            # Unlit background dust particle: dim teal, barely visible
            py5.fill(210, 40, 25, 4.0 * breath)
            py5.circle(x, y, rad * 0.7)

    # Save frames for video compilation
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)

    # Progress feedback
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
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        print("[Render Complete] Video and preview successfully generated.")
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
