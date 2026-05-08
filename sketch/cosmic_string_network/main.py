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
N_PARTICLES = 120_000
N_STRINGS = 12
N_LOOPS = 40
STAR_COUNT = 10_000

# State
# Strings and loops will be pre-generated as paths
string_paths = []
loop_paths = []

stars_pos = np.zeros((STAR_COUNT, 3), dtype=np.float32)
stars_mag = np.zeros(STAR_COUNT, dtype=np.float32)

def generate_path(n_points, radius=500, is_loop=False):
    points = np.random.uniform(-radius, radius, (n_points, 3))
    if is_loop:
        # Close the loop
        points[-1] = points[0]
    # Smooth with simple averaging
    for _ in range(3):
        points[1:-1] = (points[:-2] + points[1:-1] + points[2:]) / 3.0
    return points

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Init strings and loops
    for _ in range(N_STRINGS):
        string_paths.append(generate_path(50, radius=1200, is_loop=False))
    for _ in range(N_LOOPS):
        loop_paths.append(generate_path(30, radius=np.random.uniform(100, 400), is_loop=True))
        
    # Init stars
    stars_pos[:, 0] = np.random.uniform(-SIZE[0]*1.5, SIZE[0]*1.5, STAR_COUNT)
    stars_pos[:, 1] = np.random.uniform(-SIZE[1]*1.5, SIZE[1]*1.5, STAR_COUNT)
    stars_pos[:, 2] = np.random.uniform(-2500, -1000, STAR_COUNT)
    stars_mag[:] = np.random.uniform(100, 255, STAR_COUNT)


def draw():
    py5.background(0)
    
    # Camera
    t = py5.frame_count / TOTAL_FRAMES
    cam_dist = 1500
    cam_x = cam_dist * np.sin(t * 2 * np.pi * 0.1)
    cam_z = cam_dist * np.cos(t * 2 * np.pi * 0.1)
    py5.camera(cam_x, -400 * np.sin(t * 2 * np.pi * 0.05), cam_z, 0, 0, 0, 0, 1, 0)
    
    # 1. Stars
    py5.stroke_weight(1)
    for i in range(STAR_COUNT):
        twinkle = np.sin(py5.frame_count * 0.12 + i) * 60
        py5.stroke(stars_mag[i] + twinkle, 160)
        py5.point(stars_pos[i, 0], stars_pos[i, 1], stars_pos[i, 2])

    # 2. String Network
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # We'll distribute particles along the paths
    # To animate, we'll shift the sampling offset
    
    # Total particles split between strings and loops
    p_per_string = N_PARTICLES // (N_STRINGS + N_LOOPS)
    
    def draw_path(path, hue_base, offset):
        n = len(path)
        # Vectorized sampling along the path
        # Using linear interpolation between points
        
        # indices for segments
        idx = np.linspace(0, n - 1, p_per_string)
        idx_low = idx.astype(np.int32)
        idx_high = np.clip(idx_low + 1, 0, n - 1)
        frac = (idx - idx_low)[:, None]
        
        # Particles positions
        p_pos = path[idx_low] * (1 - frac) + path[idx_high] * frac
        
        # Add noise/jitter based on frame count
        noise = (np.random.normal(0, 2, p_pos.shape) * 
                 np.sin(py5.frame_count * 0.2 + idx[:, None] * 0.5))
        p_pos += noise
        
        # Brightness peaks (cusps)
        cusp_pos = np.sin(py5.frame_count * 0.05 + idx * 0.2)
        cusp_mask = cusp_pos > 0.8
        
        py5.begin_shape(py5.POINTS)
        for i in range(0, p_per_string, 4):
            # Spectral colors
            h = (hue_base + np.sin(idx[i] * 0.1) * 20) % 360
            s = 40 + 60 * (1 - cusp_pos[i])
            b = 60 + 40 * cusp_pos[i]
            a = 10 + 60 * cusp_pos[i]
            
            if cusp_mask[i]:
                py5.stroke(0, 0, 100, 100) # Blinding White
                py5.stroke_weight(2)
            else:
                py5.stroke(h, s, b, a)
                py5.stroke_weight(1)
                
            py5.vertex(p_pos[i, 0], p_pos[i, 1], p_pos[i, 2])
        py5.end_shape()

    # Draw infinite strings (Cyan/Indigo)
    for i, path in enumerate(string_paths):
        # Slightly oscillate the path
        offset_path = path + 20 * np.sin(py5.frame_count * 0.02 + i)
        draw_path(offset_path, 190, i * 10)
        
    # Draw loops (Amethyst/Violet)
    for i, path in enumerate(loop_paths):
        # Loops shrink/expand or drift
        drift = np.array([50 * np.sin(t * 2 * np.pi + i), 0, 50 * np.cos(t * 2 * np.pi + i)])
        draw_path(path + drift, 280, i * 5)
    
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
