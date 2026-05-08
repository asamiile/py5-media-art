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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Tesseract Parameters
NUM_PARTICLES = 200_000
DIM = 4

# State
pts_4d = None
stars = None

def setup():
    global pts_4d, stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Sample points on the faces of a 4D hypercube
    # A tesseract has 8 cubic cells as faces.
    # We'll sample points on these cubes.
    pts = []
    points_per_face = NUM_PARTICLES // 8
    for i in range(8):
        # Each face is at one coordinate = +/- 1
        # and other 3 coordinates in [-1, 1]
        face_idx = i // 2
        val = 1.0 if i % 2 == 0 else -1.0
        
        face_pts = np.random.uniform(-1, 1, (points_per_face, 4))
        face_pts[:, face_idx] = val
        pts.append(face_pts)
    
    pts_4d = np.concatenate(pts, axis=0).astype(np.float32)
    
    # Stars
    num_stars = 12000
    star_pos = np.random.uniform(-1500, 1500, (num_stars, 3))
    star_mag = np.random.uniform(0.5, 2.5, num_stars)
    stars = (star_pos, star_mag)

def rotate_4d(pts, angle_xy, angle_zw):
    # XY Rotation
    c, s = np.cos(angle_xy), np.sin(angle_xy)
    new_pts = pts.copy()
    new_pts[:, 0] = pts[:, 0] * c - pts[:, 1] * s
    new_pts[:, 1] = pts[:, 0] * s + pts[:, 1] * c
    
    # ZW Rotation
    c, s = np.cos(angle_zw), np.sin(angle_zw)
    tmp_z = new_pts[:, 2] * c - new_pts[:, 3] * s
    new_pts[:, 3] = new_pts[:, 2] * s + new_pts[:, 3] * c
    new_pts[:, 2] = tmp_z
    
    return new_pts

def project_4d_to_3d(pts, distance=2.5):
    # Perspective projection from 4D to 3D
    # Using w (pts[:, 3]) as the 4th dimension
    w = pts[:, 3]
    factor = 1.0 / (distance - w)
    proj = pts[:, :3] * factor[:, np.newaxis]
    return proj * 300 # Scale for view

def draw():
    py5.background(2, 5, 10)  # Deep Obsidian
    
    # Camera
    t = py5.frame_count / 60.0
    py5.camera(600 * np.cos(t * 0.1), -200 + 100 * np.sin(t * 0.2), 600 * np.sin(t * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke_weight(1)
    for p, m in zip(stars[0], stars[1]):
        alpha = 150 + 100 * np.sin(t * 5 + m * 10)
        py5.stroke(200, 230, 255, alpha)
        py5.point(*p)

    # 4D Rotation
    angle_xy = t * 0.5
    angle_zw = t * 0.8
    rotated = rotate_4d(pts_4d, angle_xy, angle_zw)
    
    # 3D Projection
    projected = project_4d_to_3d(rotated)
    
    # Rendering
    # Color based on W coordinate (before projection)
    w_coords = rotated[:, 3]
    # Normalize W to [0, 1]
    norm_w = (w_coords + 1) / 2.0
    
    # Multi-pass rendering for spectral effect
    bands = 10
    for i in range(bands):
        mask = (norm_w >= i / bands) & (norm_w < (i + 1) / bands)
        if not np.any(mask): continue
        
        # Color: Indigo -> Violet -> Gold
        # Use HSB mapping
        hue = 180 + i * 8 # 180 (Cyan) to 260 (Indigo/Violet)
        sat = 80
        bri = 100
        
        # Or just manual HSB/RGB
        # i=0: Indigo (280)
        # i=9: Gold (50)
        h = (280 - i * 23) % 360
        py5.color_mode(py5.HSB, 360, 100, 100, 255)
        py5.stroke(h, 80, 100, 150)
        py5.stroke_weight(1.5)
        py5.points(projected[mask])
        py5.color_mode(py5.RGB, 255, 255, 255, 255)

    # Post-process frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # FFmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264", "-crf", "30", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
