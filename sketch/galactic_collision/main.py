import numpy as np
from pathlib import Path
import subprocess
import sys
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

# Simulation Parameters
NUM_PARTICLES_A = 60000
NUM_PARTICLES_B = 60000
G = 1.2
SOFTENING = 60.0 

# State
pos = None
vel = None
starfield = None

def create_galaxy(center, num_particles, radius_max, base_vel, rotation_axis):
    # Log-normal distribution for radius
    r = np.random.lognormal(mean=np.log(radius_max*0.4), sigma=0.6, size=num_particles)
    r = r[r < radius_max]
    num_particles = len(r)
    
    theta = np.random.uniform(0, 2 * np.pi, num_particles)
    
    # 2D coordinates in its own plane
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.random.normal(0, 20, num_particles)
    
    p = np.stack([x, y, z], axis=-1)
    
    # Rotation
    if rotation_axis == 'x':
        p = p[:, [0, 2, 1]]
    elif rotation_axis == 'y':
        p = p[:, [2, 1, 0]]
    
    p += center
    
    # Velocity: Circular orbit + base drift
    v_mag = np.sqrt(G * 150000 / (r + SOFTENING))
    vx = -v_mag * np.sin(theta)
    vy = v_mag * np.cos(theta)
    vz = np.random.normal(0, 2, num_particles)
    
    v = np.stack([vx, vy, vz], axis=-1)
    if rotation_axis == 'x':
        v = v[:, [0, 2, 1]]
    elif rotation_axis == 'y':
        v = v[:, [2, 1, 0]]
    
    v += base_vel
    
    return p, v

def setup():
    global pos, vel, starfield
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Galaxy A
    pA, vA = create_galaxy(np.array([-500, -300, 0]), NUM_PARTICLES_A, 800, np.array([3.0, 2.0, 0.5]), 'z')
    
    # Galaxy B
    pB, vB = create_galaxy(np.array([500, 300, -200]), NUM_PARTICLES_B, 700, np.array([-3.0, -2.0, -0.5]), 'x')
    
    pos = np.vstack([pA, pB]).astype(np.float32)
    vel = np.vstack([vA, vB]).astype(np.float32)
    
    # Starfield
    num_stars = 3000
    sx = np.random.uniform(-py5.width*2, py5.width*2, num_stars)
    sy = np.random.uniform(-py5.height*2, py5.height*2, num_stars)
    sz = np.random.uniform(-3000, 500, num_stars)
    sb = np.random.uniform(20, 90, num_stars)
    starfield = np.stack([sx, sy, sz, sb], axis=-1)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos, vel
    
    # Physics: Gravity towards centroids
    centroid_a = np.mean(pos[:NUM_PARTICLES_A], axis=0)
    centroid_b = np.mean(pos[NUM_PARTICLES_A:], axis=0)
    
    # All particles attracted to both centroids
    for c, m in [(centroid_a, 180000.0), (centroid_b, 150000.0)]:
        diff = c - pos
        dist_sq = np.sum(diff**2, axis=-1) + SOFTENING**2
        dist = np.sqrt(dist_sq)
        force_mag = G * m / dist_sq
        acc = (diff / dist[:, np.newaxis]) * force_mag[:, np.newaxis]
        vel += acc
    
    # Friction/Drag to keep it stable
    vel *= 0.998
    pos += vel
    
    # Render
    py5.background(0)
    
    # Starfield
    py5.push_matrix()
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[3], 60)
        py5.point(s[0], s[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1000)
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_x(0.4 + py5.frame_count * 0.001)
    
    # Galaxy A: Cyan
    py5.stroke_weight(1.5)
    # Core
    py5.stroke(190, 70, 100, 80)
    py5.points(pos[:NUM_PARTICLES_A:2])
    # Faint outer
    py5.stroke(210, 40, 80, 30)
    py5.points(pos[1:NUM_PARTICLES_A:4])
    
    # Galaxy B: Magenta
    # Core
    py5.stroke(310, 70, 100, 80)
    py5.points(pos[NUM_PARTICLES_A::2])
    # Faint outer
    py5.stroke(330, 40, 80, 30)
    py5.points(pos[NUM_PARTICLES_A+1::4])

    # Centroid Glows
    for c, h in [(centroid_a, 190), (centroid_b, 310)]:
        py5.push_matrix()
        py5.translate(c[0], c[1], c[2])
        py5.no_stroke()
        for r in range(4):
            py5.fill(h, 20, 100, 12 - r*3)
            py5.sphere(60 + r*25)
        py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
