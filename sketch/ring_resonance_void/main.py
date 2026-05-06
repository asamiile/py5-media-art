from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
PARTICLE_COUNT = 180000
STAR_COUNT = 6000
RING_INNER = 180
RING_OUTER = 450
PLANET_RADIUS = 150

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, angles, radial_dist, stars, moons
    # Rings in (r, theta) coordinates
    # Using a slightly non-uniform distribution to create "gaps"
    radial_dist = np.random.uniform(RING_INNER, RING_OUTER, PARTICLE_COUNT)
    # Add a gap
    gap_center = 300
    gap_width = 15
    mask = (radial_dist > gap_center - gap_width/2) & (radial_dist < gap_center + gap_width/2)
    radial_dist[mask] += np.random.uniform(gap_width, gap_width*2, np.sum(mask))
    
    angles = np.random.uniform(0, 2 * np.pi, PARTICLE_COUNT)
    
    # Moons: [angle, radius, mass_factor]
    moons = np.array([
        [0.0, 310, 1.5],
        [np.pi, 420, 2.0]
    ])
    
    # Stars
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    global angles, radial_dist
    py5.background(5, 5, 10)
    
    time_val = py5.frame_count / 60.0
    
    # Update Moons
    moons[0, 0] += 0.02 # Angular speed
    moons[1, 0] += 0.012
    
    # Update Particles (Keplerian-ish rotation)
    # Speed is proportional to 1/sqrt(r)
    speeds = 5.0 / np.sqrt(radial_dist)
    angles += speeds * 0.1
    
    # Perturbations (Wakes)
    # Each moon creates a local radial shift
    r_perturbed = radial_dist.copy()
    for m_ang, m_r, m_mass in moons:
        # Distance in angle
        d_ang = angles - m_ang
        # High-frequency wave near moon
        wake = m_mass * 5.0 * np.sin(d_ang * 20.0) * np.exp(-np.abs(radial_dist - m_r) / 10.0)
        r_perturbed += wake
    
    # Cartesian mapping
    x = r_perturbed * np.cos(angles)
    y = np.random.normal(0, 1, PARTICLE_COUNT) # Very thin disk
    z = r_perturbed * np.sin(angles)
    
    # Camera
    cam_dist = 1000 + py5.sin(time_val * 0.2) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               -500, 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 120)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Rings (Additive)
    py5.blend_mode(py5.ADD)
    # Use points() for speed
    points = np.stack([x, y, z], axis=1)
    
    # Colors: alternating between gold and ice-blue based on radius
    py5.stroke_weight(1)
    
    # Split into two groups for color mapping
    mask_gold = (radial_dist % 20) < 10
    
    py5.stroke(238, 232, 170, 40) # Pale Gold
    py5.points(points[mask_gold])
    
    py5.stroke(153, 255, 255, 30) # Ice Blue
    py5.points(points[~mask_gold])
    
    py5.blend_mode(py5.BLEND)
    
    # 3. Planet Shadow (Approximate with a dark box or sector)
    # The planet casts a shadow away from a light source
    # Let's say light is at (-1000, 0, 0)
    py5.push_matrix()
    py5.rotate_y(py5.PI)
    py5.no_stroke()
    py5.fill(0, 0, 0, 180)
    # Simplified shadow as a dark box stretching across the ring
    py5.translate(300, 0, 0)
    py5.box(400, 10, 200)
    py5.pop_matrix()
    
    # 4. Central Planet (Dark Silhouette)
    py5.fill(10, 10, 15)
    py5.no_stroke()
    py5.sphere(PLANET_RADIUS)
    # Atmospheric glow
    for i in range(3):
        r_glow = PLANET_RADIUS * (1.0 + i * 0.05)
        py5.fill(100, 100, 255, 20)
        py5.sphere(r_glow)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "10M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
