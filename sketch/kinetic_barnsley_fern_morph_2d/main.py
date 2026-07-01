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
NUM_POINTS = 300000
points = np.zeros((NUM_POINTS, 2))

# Standard Barnsley Fern affine transformations
# Each is [a, b, c, d, e, f, p]
# x = ax + by + e
# y = cx + dy + f
# p is probability
standard_matrices = np.array([
    [0.00,  0.00,  0.00, 0.16, 0.00, 0.00,  0.01], # Stem
    [0.85,  0.04, -0.04, 0.85, 0.00, 1.60,  0.85], # Successive leaflets
    [0.20, -0.26,  0.23, 0.22, 0.00, 1.60,  0.07], # Largest left-hand leaflet
    [-0.15, 0.28,  0.26, 0.24, 0.00, 0.44,  0.07]  # Largest right-hand leaflet
])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize near origin
    points[:, 0] = np.random.uniform(-1, 1, NUM_POINTS)
    points[:, 1] = np.random.uniform(-1, 1, NUM_POINTS)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10, 5, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # Modulate matrices to mutate the fern
    mutated_matrices = np.copy(standard_matrices)
    
    # Let the fern "breathe" and sway in the wind
    sway = np.sin(t) * 0.05
    curl = np.cos(t * 0.5) * 0.05
    
    # Stem mutation
    mutated_matrices[0, 3] = 0.16 + np.sin(t * 2.0) * 0.02 
    
    # Leaflet mutations
    mutated_matrices[1, 1] += sway
    mutated_matrices[1, 2] -= sway
    
    mutated_matrices[2, 0] += curl
    mutated_matrices[3, 0] -= curl
    
    # Normalize probabilities just in case
    probs = mutated_matrices[:, 6]
    probs /= np.sum(probs)
    
    # We apply the IFS iteratively a few times per frame to ensure convergence and chaotic mixing
    for _ in range(4):
        # Pick transformation for each point
        r = np.random.random(NUM_POINTS)
        
        # Cumulative probabilities
        c_probs = np.cumsum(probs)
        
        # Create masks
        m0 = r < c_probs[0]
        m1 = (r >= c_probs[0]) & (r < c_probs[1])
        m2 = (r >= c_probs[1]) & (r < c_probs[2])
        m3 = r >= c_probs[2]
        
        x = points[:, 0].copy()
        y = points[:, 1].copy()
        
        def apply_transform(mask, idx):
            if np.any(mask):
                a, b, c, d, e, f, _ = mutated_matrices[idx]
                points[mask, 0] = a * x[mask] + b * y[mask] + e
                points[mask, 1] = c * x[mask] + d * y[mask] + f
                
        apply_transform(m0, 0)
        apply_transform(m1, 1)
        apply_transform(m2, 2)
        apply_transform(m3, 3)

    # Scale and center
    # Original fern X is roughly [-2.18, 2.65], Y is [0, 9.99]
    scale_y = SIZE[1] * 0.85 / 10.0
    scale_x = scale_y
    
    x2d = points[:, 0] * scale_x + SIZE[0]/2
    y2d = SIZE[1] - (points[:, 1] * scale_y + SIZE[1]*0.05)
    
    # Segment coloring: we color points based on which transformation they just underwent
    # Because we do 4 iterations per frame, we color based on the last applied mask
    py5.stroke_weight(2)
    
    # Stem & Main leaves (m0, m1) -> glowing green
    mask_green = m0 | m1
    if np.any(mask_green):
        py5.stroke(50, 255, 100, 40)
        pts = np.column_stack((x2d[mask_green], y2d[mask_green]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Left branches (m2) -> glowing cyan/blue
    if np.any(m2):
        py5.stroke(0, 200, 255, 40)
        pts = np.column_stack((x2d[m2], y2d[m2]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Right branches (m3) -> glowing yellow/green
    if np.any(m3):
        py5.stroke(200, 255, 0, 40)
        pts = np.column_stack((x2d[m3], y2d[m3]))
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
