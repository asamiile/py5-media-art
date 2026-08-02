from pathlib import Path
import sys
import random
import math
import subprocess
import shutil
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes
from lib.animation import frames_dir

# Directories and parameters
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

FPS = 60
TOTAL_FRAMES = 900  # 15 seconds
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Obstacle/Portal definitions
# (x, y, radius)
PORTALS = [
    (1920, 1000, 280),  # Central main portal
    (1200, 1250, 200),  # Left portal
    (2640, 1250, 200),  # Right portal
]

class Leaf:
    def __init__(self, x, y, angle, hue, max_size):
        self.x = x
        self.y = y
        self.angle = angle
        self.hue = hue
        self.max_size = max_size
        self.phase = random.uniform(0, math.pi * 2)
        self.age = 0
        self.lifetime = random.randint(180, 300)

class Tendril:
    def __init__(self, x, y, vx, vy, hue):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.history = [(x, y)]
        self.age = 0
        self.alive = True
        self.hue = hue
        self.branch_delay = 40

# State
tendrils = []
leaves = []

# Background star particles to give deep slate wall texture
background_particles_x = []
background_particles_y = []
background_particles_brightness = []

# Generative seed (ensures no fixed seeds)
SEED = random.randint(0, 1000000)
rng = np.random.RandomState(SEED)

def setup():
    global tendrils, background_particles_x, background_particles_y, background_particles_brightness
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Pre-render deep background once
    py5.background(220, 15, 6)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create background texture particles
    for _ in range(1200):
        background_particles_x.append(rng.uniform(0, py5.width))
        background_particles_y.append(rng.uniform(0, py5.height))
        background_particles_brightness.append(rng.uniform(10, 22))
        
    # Spawn initial tendrils at the bottom
    n_roots = 20
    for i in range(n_roots):
        x = py5.width * (0.1 + 0.8 * (i / (n_roots - 1))) + rng.uniform(-20, 20)
        y = py5.height - rng.uniform(10, 40)
        vx = rng.uniform(-0.5, 0.5)
        vy = rng.uniform(-1.5, -2.5)
        hue = rng.uniform(138, 162)
        tendrils.append(Tendril(x, y, vx, vy, hue))

def draw_portals():
    # Draw glowing violet/magenta neon rings
    py5.no_fill()
    for px, py, pr in PORTALS:
        # Glow pass 1 (thicker, low-alpha)
        py5.stroke(320, 85, 90, 8)
        py5.stroke_weight(18.0)
        py5.circle(px, py, pr * 2)
        
        # Glow pass 2 (medium)
        py5.stroke(320, 85, 95, 25)
        py5.stroke_weight(6.0)
        py5.circle(px, py, pr * 2)
        
        # Core pass (sharp, bright)
        py5.stroke(320, 60, 100, 85)
        py5.stroke_weight(1.5)
        py5.circle(px, py, pr * 2)

def update_simulation():
    global tendrils, leaves
    
    # 1. Update tendril physics
    next_tendrils = []
    for t in tendrils:
        if not t.alive:
            continue
            
        t.age += 1
        t.branch_delay = max(0, t.branch_delay - 1)
        
        # Simplex/Perlin noise wander force
        noise_angle = py5.noise(t.x * 0.003, t.y * 0.003, py5.frame_count * 0.004) * py5.TWO_PI * 1.5
        wx = py5.cos(noise_angle) * 0.32
        wy = py5.sin(noise_angle) * 0.32
        
        # Upward bias
        ux, uy = 0.0, -0.18
        
        # Obstacle avoidance force
        ax, ay = 0.0, 0.0
        for px, py, pr in PORTALS:
            dx = t.x - px
            dy = t.y - py
            dist = math.hypot(dx, dy)
            if dist < 0.001:
                dist = 0.001
            
            # Repulsion from inside the portal
            if dist < pr:
                ax += (dx / dist) * 1.8
                ay += (dy / dist) * 1.8
            # Align and slide along the rim outside
            elif dist < pr + 75:
                overlap = (pr + 75) - dist
                ax += (dx / dist) * overlap * 0.038
                ay += (dy / dist) * overlap * 0.038
                
        # Apply forces
        t.vx += wx + ux + ax
        t.vy += wy + uy + ay
        
        # Speed limit
        speed = math.hypot(t.vx, t.vy)
        max_speed = 2.4
        if speed > max_speed:
            t.vx = (t.vx / speed) * max_speed
            t.vy = (t.vy / speed) * max_speed
            
        # Move
        prev_x, prev_y = t.x, t.y
        t.x += t.vx
        t.y += t.vy
        t.history.append((t.x, t.y))
        if len(t.history) > 10:
            t.history.pop(0)
            
        # Die if out of bounds or too old
        if t.y < 30 or t.x < 30 or t.x > py5.width - 30 or t.age > 850:
            t.alive = False
            continue
            
        # Draw vine segment
        alpha = py5.remap(t.age, 0, 850, 80, 20)
        weight = py5.remap(t.age, 0, 850, 4.0, 0.8)
        
        # Additive vine glow
        py5.stroke(t.hue, 80, 70, alpha * 0.2)
        py5.stroke_weight(weight * 3.0)
        py5.line(prev_x, prev_y, t.x, t.y)
        
        py5.stroke(t.hue, 80, 80, alpha)
        py5.stroke_weight(weight)
        py5.line(prev_x, prev_y, t.x, t.y)
        
        # Spawn leaf occasionally
        if t.age % 18 == 0:
            angle = math.atan2(t.vy, t.vx) - math.pi / 2.0
            leaf_hue = t.hue + rng.uniform(-10, 10)
            max_size = rng.uniform(10, 22)
            leaves.append(Leaf(t.x, t.y, angle, leaf_hue, max_size))
            
        # Branching behavior
        if t.age > 60 and t.branch_delay == 0 and len(tendrils) < 80:
            if rng.random() < 0.024:
                # Spawn branch
                branch_angle = rng.choice([-0.8, 0.8]) * rng.uniform(0.4, 0.8)
                c, s = math.cos(branch_angle), math.sin(branch_angle)
                bvx = t.vx * c - t.vy * s
                bvy = t.vx * s + t.vy * c
                next_tendrils.append(Tendril(t.x, t.y, bvx, bvy, t.hue))
                t.branch_delay = 50
                
        next_tendrils.append(t)
        
    tendrils = next_tendrils

def draw_leaves():
    # Update and draw leaves with wind sway
    for l in leaves:
        l.age += 1
        # Leaf scale grows when born and decays slowly at the end
        if l.age < 30:
            scale = l.age / 30.0
        else:
            scale = max(0.0, 1.0 - (l.age - 30) / (l.lifetime - 30))
            
        current_size = l.max_size * scale
        if current_size <= 0.1:
            continue
            
        # Wind sway
        wind = math.sin(py5.frame_count * 0.045 + l.phase) * 0.14
        
        py5.push_matrix()
        py5.translate(l.x, l.y)
        py5.rotate(l.angle + wind)
        
        # Glow pass (translucent, soft green)
        py5.no_stroke()
        py5.fill(l.hue, 85, 75, 12)
        py5.begin_shape()
        py5.vertex(0, 0)
        py5.bezier_vertex(current_size * 0.7, -current_size * 0.4, current_size * 0.7, -current_size * 1.1, 0, -current_size * 1.4)
        py5.bezier_vertex(-current_size * 0.7, -current_size * 1.1, -current_size * 0.7, -current_size * 0.4, 0, 0)
        py5.end_shape(py5.CLOSE)
        
        # Sharp blade pass
        py5.fill(l.hue, 80, 82, 70)
        py5.begin_shape()
        py5.vertex(0, 0)
        py5.bezier_vertex(current_size * 0.45, -current_size * 0.35, current_size * 0.45, -current_size * 0.95, 0, -current_size * 1.25)
        py5.bezier_vertex(-current_size * 0.45, -current_size * 0.95, -current_size * 0.45, -current_size * 0.35, 0, 0)
        py5.end_shape(py5.CLOSE)
        
        # Solar Gold center vein (fine detail)
        py5.stroke(45, 90, 100, 80)
        py5.stroke_weight(0.9)
        py5.line(0, 0, 0, -current_size * 1.1)
        
        py5.pop_matrix()

def draw():
    # Draw background slate wall with persistent texture
    # Clean background slightly each frame for motion trails on moving elements
    py5.fill(220, 15, 6, 22)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Render static textured particles with subtle twinkle
    for i in range(1200):
        brightness = background_particles_brightness[i] + 4.0 * math.sin(py5.frame_count * 0.03 + i)
        py5.stroke(220, 15, brightness, 140)
        py5.stroke_weight(1.2)
        py5.point(background_particles_x[i], background_particles_y[i])
        
    # Draw structural neon portals
    draw_portals()
    
    # Update and draw vines
    update_simulation()
    
    # Draw leaves
    draw_leaves()
    
    # Fail-safe standard deviation check
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
        
    # Compile video on last frame
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot at mid-point
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Cleanup temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
