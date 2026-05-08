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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
N_STARS = 3_000
N_CLUSTERS = 100_000
STAR_COUNT = 12_000
G = 100.0
SOFTENING = 20.0

# State
pos = np.zeros((N_STARS, 3), dtype=np.float32)
vel = np.zeros((N_STARS, 3), dtype=np.float32)
mass = np.random.uniform(1, 5, N_STARS)

cluster_pos = np.zeros((N_CLUSTERS, 3), dtype=np.float32)
stars_pos = np.zeros((STAR_COUNT, 3), dtype=np.float32)
stars_mag = np.zeros(STAR_COUNT, dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Init N-stars
    # Spherical distribution
    r = np.random.uniform(0, 800, N_STARS)
    phi = np.arccos(np.random.uniform(-1, 1, N_STARS))
    theta = np.random.uniform(0, 2 * np.pi, N_STARS)
    
    pos[:, 0] = r * np.sin(phi) * np.cos(theta)
    pos[:, 1] = r * np.sin(phi) * np.sin(theta)
    pos[:, 2] = r * np.cos(phi)
    
    # Circular velocity approx: v ~ sqrt(GM/r)
    v_mag = np.sqrt(G * 5000 / (r + 100))
    vel[:, 0] = -v_mag * np.sin(theta)
    vel[:, 1] = v_mag * np.cos(theta)
    vel[:, 2] = np.random.normal(0, 1, N_STARS)
    
    # Init Cluster background
    cr = np.random.normal(0, 400, N_CLUSTERS)
    cphi = np.arccos(np.random.uniform(-1, 1, N_CLUSTERS))
    ctheta = np.random.uniform(0, 2 * np.pi, N_CLUSTERS)
    cluster_pos[:, 0] = cr * np.sin(cphi) * np.cos(ctheta)
    cluster_pos[:, 1] = cr * np.sin(cphi) * np.sin(ctheta)
    cluster_pos[:, 2] = cr * np.cos(cphi)
    
    # Init stars
    stars_pos[:, 0] = np.random.uniform(-SIZE[0]*1.5, SIZE[0]*1.5, STAR_COUNT)
    stars_pos[:, 1] = np.random.uniform(-SIZE[1]*1.5, SIZE[1]*1.5, STAR_COUNT)
    stars_pos[:, 2] = np.random.uniform(-3000, -1000, STAR_COUNT)
    stars_mag[:] = np.random.uniform(80, 255, STAR_COUNT)


def draw():
    global pos, vel
    py5.background(0)
    
    # Camera
    t = py5.frame_count / TOTAL_FRAMES
    cam_dist = 1200 + 300 * np.sin(t * 2 * np.pi)
    cam_x = cam_dist * np.sin(t * 2 * np.pi * 0.05)
    cam_z = cam_dist * np.cos(t * 2 * np.pi * 0.05)
    py5.camera(cam_x, -300 * np.cos(t * 2 * np.pi * 0.1), cam_z, 0, 0, 0, 0, 1, 0)
    
    # 1. Background Stars
    py5.stroke_weight(1)
    for i in range(STAR_COUNT):
        twinkle = np.sin(py5.frame_count * 0.07 + i) * 50
        py5.stroke(stars_mag[i] + twinkle, 140)
        py5.point(stars_pos[i, 0], stars_pos[i, 1], stars_pos[i, 2])

    # 2. Cluster Cloud (static but twinkling)
    py5.stroke_weight(1)
    # Sub-sample for performance
    for i in range(0, N_CLUSTERS, 10):
        d_sq = np.sum(cluster_pos[i]**2)
        bri = np.interp(d_sq, [0, 800**2], [150, 0])
        tw = np.sin(py5.frame_count * 0.1 + i) * 20
        py5.stroke(255, 240, 200, bri + tw)
        py5.point(cluster_pos[i, 0], cluster_pos[i, 1], cluster_pos[i, 2])

    # 3. N-body Dynamics (Simplified to Central potential for stability/speed)
    r_vec = -pos
    r_sq = np.sum(r_vec**2, axis=1)[:, None] + SOFTENING**2
    r_mag = np.sqrt(r_sq)
    
    # Accel towards center
    accel = G * 10000 * r_vec / (r_mag**3)
    
    # Update
    vel += accel
    pos += vel
    
    # 4. Rendering N-stars
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.begin_shape(py5.POINTS)
    for i in range(N_STARS):
        d = np.sqrt(np.sum(pos[i]**2))
        h = np.interp(d, [0, 1000], [50, 200]) # Gold to Cyan
        s = np.interp(d, [0, 1000], [20, 80])
        b = np.interp(d, [0, 1000], [100, 50])
        a = np.interp(d, [0, 1000], [100, 30])
        
        py5.stroke(h, s, b, a)
        if d < 150:
            py5.stroke_weight(2)
            py5.stroke(0, 0, 100, 100) # White hot core
        else:
            py5.stroke_weight(1)
            
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
    py5.end_shape()
    
    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
