from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_PARTICLES = 300000

# State
points = np.zeros((NUM_PARTICLES, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize randomly
    points[:, 0] = np.random.uniform(-1, 1, NUM_PARTICLES)
    points[:, 1] = np.random.uniform(-1, 1, NUM_PARTICLES)
    points[:, 2] = np.random.uniform(-1, 1, NUM_PARTICLES)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 2, 5, 12) # very dark blue trail
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # 3D Chaotic Attractor Parameters
    # We mutate these slowly to create an organic, morphing cloud
    a = 1.2 + np.sin(t * 0.5) * 0.2
    b = 1.3 + np.cos(t * 0.4) * 0.2
    c = 1.4 + np.sin(t * 0.3) * 0.2
    
    d = 1.5 + np.cos(t * 0.6) * 0.2
    e = 1.6 + np.sin(t * 0.7) * 0.2
    f = 1.7 + np.cos(t * 0.8) * 0.2
    
    g = 1.1 + np.sin(t * 0.9) * 0.2
    h = 1.8 + np.cos(t * 1.0) * 0.2
    i_p = 1.9 + np.sin(t * 1.1) * 0.2

    # Evaluate the 3D map a few times per frame
    for _ in range(2):
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        
        # A custom 3D trigonometric map (similar to Peter de Jong / Clifford)
        nx = np.sin(a * y) - np.cos(b * x) - np.sin(c * z)
        ny = np.sin(d * x) - np.cos(e * y) - np.sin(f * z)
        nz = np.sin(g * y) - np.cos(h * z) - np.sin(i_p * x)
        
        points[:, 0] = nx
        points[:, 1] = ny
        points[:, 2] = nz

    # 3D Rotation
    rot_y = t * 0.2
    rot_x = t * 0.1
    
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    
    cos_ry = np.cos(rot_y)
    sin_ry = np.sin(rot_y)
    x_rot1 = x * cos_ry - z * sin_ry
    z_rot1 = x * sin_ry + z * cos_ry
    
    cos_rx = np.cos(rot_x)
    sin_rx = np.sin(rot_x)
    y_rot2 = y * cos_rx - z_rot1 * sin_rx
    z_rot2 = y * sin_rx + z_rot1 * cos_rx
    
    # Perspective projection
    # The attractor values are roughly bounded within [-3, 3]
    scale_factor = SIZE[1] * 0.25
    fov = 1200.0
    z_offset = 6.0
    
    z_proj = z_rot2 + z_offset
    z_proj = np.maximum(z_proj, 0.1)
    
    x2d = (x_rot1 / z_proj) * fov * 3.0 + SIZE[0]/2
    y2d = SIZE[1]/2 - (y_rot2 / z_proj) * fov * 3.0
    
    py5.stroke_weight(1.5)
    
    # Spatial Coloring (mapping Z-depth to Cyan/Magenta/Gold gradients)
    mask_c1 = z_rot2 > 1.0
    mask_c2 = (z_rot2 <= 1.0) & (z_rot2 > -1.0)
    mask_c3 = z_rot2 <= -1.0
    
    if np.any(mask_c1):
        py5.stroke(0, 255, 200, 15) # Cyan (Foreground)
        pts = np.column_stack((x2d[mask_c1], y2d[mask_c1]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    if np.any(mask_c2):
        py5.stroke(255, 0, 150, 15) # Magenta (Midground)
        pts = np.column_stack((x2d[mask_c2], y2d[mask_c2]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    if np.any(mask_c3):
        py5.stroke(255, 200, 0, 15) # Gold (Background)
        pts = np.column_stack((x2d[mask_c3], y2d[mask_c3]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

py5.run_sketch()
