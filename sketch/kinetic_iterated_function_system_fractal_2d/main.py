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

# Chaos game parameters
NUM_PARTICLES = 100_000
ITERS_PER_FRAME = 1

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points
    points = np.random.uniform(-1, 1, (NUM_PARTICLES, 2))

def draw():
    # Dim background slightly for motion blur and density accumulation
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # 3 Affine transforms that morph over time
    # Transform 1: scale and rotate
    theta1 = t * py5.TWO_PI
    s1 = 0.5 + 0.1 * np.sin(t * py5.TWO_PI * 2)
    A1 = np.array([[np.cos(theta1), -np.sin(theta1)], 
                   [np.sin(theta1),  np.cos(theta1)]]) * s1
    B1 = np.array([0.5 * np.cos(t * py5.TWO_PI), 0.5 * np.sin(t * py5.TWO_PI)])
    
    # Transform 2
    theta2 = -t * py5.TWO_PI * 1.5 + 1.0
    s2 = 0.5 + 0.1 * np.cos(t * py5.TWO_PI)
    A2 = np.array([[np.cos(theta2), -np.sin(theta2)], 
                   [np.sin(theta2),  np.cos(theta2)]]) * s2
    B2 = np.array([-0.5, -0.5])
    
    # Transform 3
    theta3 = t * py5.TWO_PI * 0.5 - 0.5
    s3 = 0.5
    A3 = np.array([[np.cos(theta3), -np.sin(theta3)], 
                   [np.sin(theta3),  np.cos(theta3)]]) * s3
    B3 = np.array([0.0, 0.5 + 0.2 * np.sin(t * py5.TWO_PI)])
    
    transforms = [(A1, B1), (A2, B2), (A3, B3)]
    colors = [(255, 100, 50), (50, 200, 255), (200, 50, 255)] # Orange, Cyan, Purple
    
    global points
    
    py5.stroke_weight(1)
    
    for _ in range(ITERS_PER_FRAME):
        # Pick random transform for each point
        idx = np.random.randint(0, 3, size=NUM_PARTICLES)
        
        new_points = np.empty_like(points)
        
        for k in range(3):
            mask = idx == k
            if not np.any(mask): continue
            A, B = transforms[k]
            # p' = A * p + B
            # p is (N, 2), A is (2, 2)
            new_points[mask] = points[mask] @ A.T + B
            
        points = new_points
        
        # Now map to screen space and draw
        # Coordinates are roughly -2 to 2
        screen_x = (points[:, 0] * py5.height * 0.4) + py5.width / 2
        screen_y = (points[:, 1] * py5.height * 0.4) + py5.height / 2
        
        pts = np.column_stack((screen_x, screen_y))
        
        # Draw with different colors per transform group
        for k in range(3):
            mask = idx == k
            pts_k = pts[mask]
            c = colors[k]
            py5.stroke(c[0], c[1], c[2], 10)
            if len(pts_k) > 0:
                py5.points(pts_k)
                
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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
