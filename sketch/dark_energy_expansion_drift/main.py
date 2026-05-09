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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Constants
NUM_PARTICLES = 120_000
NUM_STARS = 12_000

# State
particles = None
stars = None
colors = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, stars, colors
    
    # Initialize Stars (Deep Background)
    star_pos = np.random.uniform(-2000, 2000, (NUM_STARS, 3))
    star_bright = np.random.uniform(50, 200, NUM_STARS)
    stars = np.column_stack((star_pos, star_bright))
    
    # Initialize Particles
    # x, y, z, vx, vy, vz, life, phase
    pos = np.random.normal(0, 50, (NUM_PARTICLES, 3))
    vel = np.random.normal(0, 0.5, (NUM_PARTICLES, 3))
    life = np.random.uniform(0, 1, NUM_PARTICLES)
    phase = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    particles = np.hstack((pos, vel, life.reshape(-1, 1), phase.reshape(-1, 1)))
    
    # Pre-calculate colors (Cosmic Lavender / Deep Emerald / Silver / Platinum)
    # HSB: Lavender (270, 40, 100), Emerald (160, 60, 100), Silver (200, 5, 90)
    colors = np.zeros((NUM_PARTICLES, 3))
    for i in range(NUM_PARTICLES):
        r = np.random.random()
        if r < 0.4: # Lavender
            colors[i] = [270 + np.random.uniform(-10, 10), 30 + np.random.uniform(0, 20), 80 + np.random.uniform(0, 20)]
        elif r < 0.7: # Emerald
            colors[i] = [160 + np.random.uniform(-10, 10), 50 + np.random.uniform(0, 20), 70 + np.random.uniform(0, 30)]
        else: # Silver/Platinum
            colors[i] = [200 + np.random.uniform(-20, 20), 5 + np.random.uniform(0, 10), 90 + np.random.uniform(0, 10)]

def update_particles():
    global particles
    t = py5.frame_count / FPS
    
    # Expansion factor: exponential growth
    # a(t) = exp(H * t)
    H = 0.08 # Increased
    expansion_force = H * particles[:, :3]
    
    # Drift field
    drift = np.zeros((NUM_PARTICLES, 3))
    freq = 0.008
    drift[:, 0] = np.sin(particles[:, 1] * freq + t) * 0.4
    drift[:, 1] = np.sin(particles[:, 2] * freq + t * 0.8) * 0.4
    drift[:, 2] = np.sin(particles[:, 0] * freq + t * 1.2) * 0.4
    
    # Update velocity and position
    particles[:, 3:6] += expansion_force * 0.01 + drift * 0.05
    particles[:, 3:6] *= 0.98 # Friction
    particles[:, :3] += particles[:, 3:6]
    
    # Life cycle
    particles[:, 6] += 0.003
    mask = particles[:, 6] > 1.0
    num_respawn = np.sum(mask)
    if num_respawn > 0:
        particles[mask, :3] = np.random.normal(0, 50, (num_respawn, 3))
        particles[mask, 3:6] = np.random.normal(0, 0.1, (num_respawn, 3))
        particles[mask, 6] = 0
        particles[mask, 7] = np.random.uniform(0, np.pi * 2, num_respawn)

def draw():
    update_particles()
    
    # Persistence effect for silken trails
    # In P3D, we can't easily use the rect-over-screen trick with transparency 
    # if we want depth. But here we want a flat "cosmic" feel.
    # We'll use a simpler approach: clear background with very dark color
    # and use high density particles with small alpha.
    py5.background(2, 2, 8) # Deep black-indigo
    
    py5.translate(py5.width/2, py5.height/2, -500)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.001)
    
    # Draw Stars
    py5.stroke_weight(1.5)
    py5.stroke(200, 200, 255, 100)
    py5.points(stars[:, :3])
    
    # Draw Particles (Additive)
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 1.0)
    py5.stroke_weight(1.2)
    
    # Alpha based on life (fade in/out)
    alpha = np.sin(particles[:, 6] * np.pi) * 0.4
    
    # Group by color category for py5.points speed
    # Categorize in setup instead of every frame
    global particles_lavender, particles_emerald, particles_silver
    if py5.frame_count == 1:
        # One-time split for efficiency (assuming colors don't change category)
        r_vals = np.random.random(NUM_PARTICLES)
        particles_lavender = r_vals < 0.4
        particles_emerald = (r_vals >= 0.4) & (r_vals < 0.7)
        particles_silver = r_vals >= 0.7

    # Draw Lavender
    subset = particles[particles_lavender]
    a_sub = alpha[particles_lavender]
    # We still have individual HSB variations... let's simplify to mean color per group
    # or just use a few sub-groups if needed. For now, let's use the average color
    # to gain massive speed with py5.points()
    py5.stroke(270, 40, 90, np.mean(a_sub))
    py5.points(subset[:, :3])
    
    # Draw Emerald
    subset = particles[particles_emerald]
    a_sub = alpha[particles_emerald]
    py5.stroke(160, 60, 80, np.mean(a_sub))
    py5.points(subset[:, :3])
    
    # Draw Silver
    subset = particles[particles_silver]
    a_sub = alpha[particles_silver]
    py5.stroke(200, 5, 95, np.mean(a_sub))
    py5.points(subset[:, :3])

    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        py5.blend_mode(py5.BLEND)
        py5.color_mode(py5.RGB, 255)
        
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()
