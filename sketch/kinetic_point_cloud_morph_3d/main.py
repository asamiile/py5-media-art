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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

FPS = 60
TOTAL_FRAMES = 900  # 15 seconds
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle count
N_PARTICLES = 15000
NUM_BINS = 12

# Generative seed (dynamic to ensure no fixed seeds)
SEED = random.randint(0, 1000000)
rng = np.random.RandomState(SEED)

# Coordinate Generators
def make_sphere(n, r_state):
    pts = r_state.standard_normal((n, 3))
    norms = np.linalg.norm(pts, axis=1, keepdims=True)
    return (pts / (norms + 1e-9)) * 0.75

def make_torus_knot(n, r_state):
    t = r_state.uniform(0, 2 * np.pi, n)
    # p=3, q=8 torus knot
    r = np.cos(8 * t) + 2.0
    x = r * np.cos(3 * t)
    y = r * np.sin(3 * t)
    z = np.sin(8 * t)
    pts = np.stack([x, y, z], axis=1)
    norms = np.linalg.norm(pts, axis=1, keepdims=True)
    return (pts / (np.max(norms) + 1e-9)) * 0.75

def make_helix(n, r_state):
    # DNA-like double helix
    pts = []
    n_half = n // 2
    for offset in [0, np.pi]:
        t = r_state.uniform(0, 4 * 2 * np.pi, n_half)
        x = np.cos(t + offset) * 0.5
        y = np.sin(t + offset) * 0.5
        z = (t / (4 * 2 * np.pi)) * 1.5 - 0.75
        # Add some noise to make it cloud-like
        x += r_state.normal(0, 0.02, n_half)
        y += r_state.normal(0, 0.02, n_half)
        z += r_state.normal(0, 0.02, n_half)
        pts.append(np.stack([x, y, z], axis=1))
    return np.concatenate(pts, axis=0).astype(np.float32)

def make_moebius(n, r_state):
    u = r_state.uniform(0, 2 * np.pi, n)
    v = r_state.uniform(-0.35, 0.35, n)
    x = (1.0 + v * np.cos(u / 2.0)) * np.cos(u)
    y = (1.0 + v * np.cos(u / 2.0)) * np.sin(u)
    z = v * np.sin(u / 2.0)
    pts = np.stack([x, y, z], axis=1)
    norms = np.linalg.norm(pts, axis=1, keepdims=True)
    return (pts / (np.max(norms) + 1e-9)) * 0.75

def make_klein_bottle(n, r_state):
    u = r_state.uniform(0, 2 * np.pi, n)
    v = r_state.uniform(0, 2 * np.pi, n)
    # Figure-8 immersion of Klein bottle
    x = (2.0 + np.cos(u / 2.0) * np.sin(v) - np.sin(u / 2.0) * np.sin(2.0 * v)) * np.cos(u)
    y = (2.0 + np.cos(u / 2.0) * np.sin(v) - np.sin(u / 2.0) * np.sin(2.0 * v)) * np.sin(u)
    z = np.sin(u / 2.0) * np.sin(v) + np.cos(u / 2.0) * np.sin(2.0 * v)
    pts = np.stack([x, y, z], axis=1)
    norms = np.linalg.norm(pts, axis=1, keepdims=True)
    return (pts / (np.max(norms) + 1e-9)) * 0.75

# Data arrays
shapes = []
point_types = np.zeros(N_PARTICLES, dtype=np.int32)
stars_x = np.zeros(600, dtype=np.float32)
stars_y = np.zeros(600, dtype=np.float32)
stars_phase = np.zeros(600, dtype=np.float32)

def setup():
    global shapes, point_types, stars_x, stars_y, stars_phase
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 40, 8)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate shapes
    shapes = [
        make_sphere(N_PARTICLES, rng),
        make_torus_knot(N_PARTICLES, rng),
        make_helix(N_PARTICLES, rng),
        make_moebius(N_PARTICLES, rng),
        make_klein_bottle(N_PARTICLES, rng)
    ]
    
    # Assign point types matching brief (60% Cyan, 30% Amethyst, 10% Gold)
    point_types = rng.choice([0, 1, 2], p=[0.6, 0.3, 0.1], size=N_PARTICLES)
    
    # Generate background stars
    stars_x = rng.uniform(0, py5.width, 600)
    stars_y = rng.uniform(0, py5.height, 600)
    stars_phase = rng.uniform(0, np.pi * 2, 600)

def project(pts, ry, rx, rz):
    """Rotate in 3D and project to 2D screen space."""
    # Rotation angles
    cy, sy = math.cos(ry), math.sin(ry)
    cx, sx = math.cos(rx), math.sin(rx)
    cz, sz = math.cos(rz), math.sin(rz)
    
    # Rotate Y
    x = pts[:, 0] * cy + pts[:, 2] * sy
    y = pts[:, 1]
    z = -pts[:, 0] * sy + pts[:, 2] * cy
    
    # Rotate X
    y2 = y * cx - z * sx
    z2 = y * sx + z * cx
    
    # Rotate Z
    x2 = x * cz - y2 * sz
    y3 = x * sz + y2 * cz
    
    # Perspective projection
    fov = 2400.0
    w2 = py5.width / 2.0
    h2 = py5.height / 2.0
    dist = z2 + 3.0
    dist = np.maximum(dist, 0.1)
    
    sx_coords = w2 + x2 * fov / dist
    sy_coords = h2 + y3 * fov / dist
    return np.stack([sx_coords, sy_coords, z2], axis=1)

def draw():
    # Subtle trails: clear the background with translucent color
    py5.fill(240, 40, 8, 25)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Twinkling stars
    for i in range(600):
        brightness = 55 + 40 * np.sin(py5.frame_count * 0.05 + stars_phase[i])
        py5.stroke(240, 20, brightness, 150)
        py5.stroke_weight(rng.uniform(1.0, 2.5))
        py5.point(stars_x[i], stars_y[i])
        
    # Morph phase calculations (5 shapes -> 5 transitions, 180 frames per transition)
    frame = (py5.frame_count - 1) % TOTAL_FRAMES
    phase_idx = frame // 180
    phase_frame = frame % 180
    
    src_shape = shapes[phase_idx]
    dst_shape = shapes[(phase_idx + 1) % len(shapes)]
    
    if phase_frame < 60:
        # Hold phase
        pts = src_shape
    else:
        # Morph phase
        t = (phase_frame - 60) / 120.0
        t_eased = t * t * (3.0 - 2.0 * t)  # Smoothstep
        pts = src_shape * (1.0 - t_eased) + dst_shape * t_eased
        
    # Spin rates
    ry = py5.frame_count * 0.012
    rx = py5.frame_count * 0.006 + 0.35
    rz = py5.frame_count * 0.003
    
    projected = project(pts, ry, rx, rz)
    
    # Render particles grouped by type and depth binned for speed
    base_hue = (py5.frame_count * 0.15) % 360
    
    for t_idx in [0, 1, 2]:
        mask = (point_types == t_idx)
        type_pts = projected[mask]
        
        if len(type_pts) == 0:
            continue
            
        # Sort current type by depth
        sort_order = np.argsort(type_pts[:, 2])[::-1]
        sorted_pts = type_pts[sort_order]
        
        # Determine base hue for this type
        if t_idx == 0:
            hue_offset = 180  # Cyan
            sat = 80
        elif t_idx == 1:
            hue_offset = 280  # Amethyst
            sat = 75
        else:
            hue_offset = 45   # Gold
            sat = 90
            
        hue = (base_hue + hue_offset) % 360
        
        # Bin points by depth
        chunks = np.array_split(sorted_pts, NUM_BINS)
        for b_idx, chunk in enumerate(chunks):
            if len(chunk) == 0:
                continue
                
            depth_t = b_idx / float(NUM_BINS - 1)
            
            # Map depth to brightness and opacity
            bright = 40 + depth_t * 60
            alpha = 15 + depth_t * 80
            
            # Draw glow pass
            py5.stroke(hue, sat, bright * 0.8, alpha * 0.15)
            py5.stroke_weight(6.0)
            py5.points(chunk[:, :2])
            
            # Draw core pass
            py5.stroke(hue, max(0, sat - 15), bright, alpha * 0.95)
            py5.stroke_weight(1.8)
            py5.points(chunk[:, :2])
            
    # Fail-safe: check standard deviation to prevent blank frames
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress indicator
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
