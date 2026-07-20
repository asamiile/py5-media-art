from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # 15-20s duration
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Variables for holographic sphere
NUM_POINTS = 20000
points = None
glitch_idx = None

def setup():
    global points
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate points on a sphere
    phi = np.arccos(1 - 2 * np.random.rand(NUM_POINTS))
    theta = 2 * np.pi * np.random.rand(NUM_POINTS)
    
    points = np.zeros((NUM_POINTS, 3))
    points[:, 0] = np.sin(phi) * np.cos(theta)
    points[:, 1] = np.sin(phi) * np.sin(theta)
    points[:, 2] = np.cos(phi)

def draw():
    global points, glitch_idx
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    
    # Base radius
    radius = min(SIZE) * 0.35
    
    # Calculate noise-based displacement
    # We will rotate the points in 3D
    rot_y = t * 0.5
    rot_x = t * 0.3
    
    # Rotation matrices
    cy, sy = np.cos(rot_y), np.sin(rot_y)
    cx, sx = np.cos(rot_x), np.sin(rot_x)
    
    Ry = np.array([
        [cy, 0, sy],
        [0, 1, 0],
        [-sy, 0, cy]
    ])
    
    Rx = np.array([
        [1, 0, 0],
        [0, cx, -sx],
        [0, sx, cx]
    ])
    
    # Apply rotations
    rotated = points @ Ry.T @ Rx.T
    
    # Add some sine wave deformations
    displacement = np.sin(rotated[:, 1] * 10 + t * 2) * 0.05 + 1.0
    
    # Glitch effect: randomly shift some points' radii
    glitch_idx = np.random.choice(NUM_POINTS, size=int(NUM_POINTS * 0.01), replace=False)
    displacement[glitch_idx] *= np.random.uniform(1.1, 1.5, size=len(glitch_idx))
    
    # Final 3D positions
    pos3d = rotated * (radius * displacement)[:, np.newaxis]
    
    # 2D projection
    z_offset = radius * 2.5
    scale = radius * 3.0 / (pos3d[:, 2] + z_offset)
    
    x2d = pos3d[:, 0] * scale + SIZE[0] / 2
    y2d = pos3d[:, 1] * scale + SIZE[1] / 2
    
    # Filter points behind camera
    valid = pos3d[:, 2] + z_offset > 0
    x2d_valid = x2d[valid]
    y2d_valid = y2d[valid]
    
    # Draw points
    py5.stroke(0, 255, 255, 150)
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for x, y in zip(x2d_valid, y2d_valid):
        py5.vertex(x, y)
    py5.end_shape()
    
    # Glitch layer
    py5.stroke(255, 0, 255, 200) # Magenta
    py5.stroke_weight(4)
    py5.begin_shape(py5.POINTS)
    # small portion for glitch
    for i in range(min(500, len(glitch_idx))):
        idx = glitch_idx[i]
        if valid[idx]:
            py5.vertex(x2d[idx], y2d[idx])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save gigabytes of local storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
