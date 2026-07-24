from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation parameters
GRID_W, GRID_H = 150, 100
REST_DIST = 15.0
TEAR_THRESHOLD = REST_DIST * 3.0
GRAVITY = np.array([0, 0.15])
DT = 0.5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, old_pos, active_h, active_v
    pos = np.zeros((GRID_H, GRID_W, 2))
    
    # Center cloth in the top portion
    start_x = (py5.width - (GRID_W - 1) * REST_DIST) / 2
    start_y = 100.0
    
    for y in range(GRID_H):
        for x in range(GRID_W):
            pos[y, x, 0] = start_x + x * REST_DIST
            pos[y, x, 1] = start_y + y * REST_DIST
            
    old_pos = pos.copy()
    
    # Active links boolean mask
    active_h = np.ones((GRID_H, GRID_W - 1, 1), dtype=bool)
    active_v = np.ones((GRID_H - 1, GRID_W, 1), dtype=bool)

def draw():
    global pos, old_pos, active_h, active_v
    
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Verlet integration
    velocity = pos - old_pos
    old_pos = pos.copy()
    pos += velocity * 0.99 + GRAVITY * DT**2
    
    # Fixed points (top row)
    pos[0, :, :] = old_pos[0, :, :]
    
    # Chaotic interaction sphere
    t = py5.frame_count / TOTAL_FRAMES
    cx = py5.width / 2 + np.sin(t * py5.TWO_PI) * 400
    cy = py5.height / 2 + np.cos(t * py5.TWO_PI * 2) * 300
    r = 250
    
    # Resolve sphere collision
    diff_c = pos - np.array([cx, cy])
    dist_c = np.linalg.norm(diff_c, axis=-1, keepdims=True)
    collide = dist_c < r
    
    # Push out of sphere
    pos = np.where(collide, pos + (diff_c / (dist_c + 1e-5)) * (r - dist_c), pos)
    
    # Relax constraints (3 iterations for stiffness)
    for _ in range(3):
        # Horizontal
        diff_h = pos[:, 1:, :] - pos[:, :-1, :]
        dist_h = np.linalg.norm(diff_h, axis=-1, keepdims=True)
        # Check tear
        active_h &= (dist_h < TEAR_THRESHOLD)
        corr_h = diff_h * ((REST_DIST - dist_h) / (dist_h + 1e-5)) * 0.5 * active_h
        
        pos[:, 1:, :] += corr_h
        pos[:, :-1, :] -= corr_h
        
        # Vertical
        diff_v = pos[1:, :, :] - pos[:-1, :, :]
        dist_v = np.linalg.norm(diff_v, axis=-1, keepdims=True)
        # Check tear
        active_v &= (dist_v < TEAR_THRESHOLD)
        corr_v = diff_v * ((REST_DIST - dist_v) / (dist_v + 1e-5)) * 0.5 * active_v
        
        pos[1:, :, :] += corr_v
        pos[:-1, :, :] -= corr_v
        
        # Keep top row fixed
        pos[0, :, :] = old_pos[0, :, :]
        
    # Render
    py5.stroke_weight(2)
    py5.no_fill()
    
    # We will draw points or lines. For a neon grid, lines are best.
    # Since drawing N*M lines individually is slow in python loops, we can use py5.begin_shape(py5.LINES)
    # Horizontal lines
    py5.stroke(180, 100, 100, 150) # Cyan
    py5.begin_shape(py5.LINES)
    # Extract points where active_h is true
    mask_h = active_h[:, :, 0]
    p1_h = pos[:, :-1, :][mask_h]
    p2_h = pos[:, 1:, :][mask_h]
    for p1, p2 in zip(p1_h, p2_h):
        py5.vertex(p1[0], p1[1])
        py5.vertex(p2[0], p2[1])
    py5.end_shape()
    
    # Vertical lines
    py5.stroke(320, 100, 100, 150) # Magenta
    py5.begin_shape(py5.LINES)
    mask_v = active_v[:, :, 0]
    p1_v = pos[:-1, :, :][mask_v]
    p2_v = pos[1:, :, :][mask_v]
    for p1, p2 in zip(p1_v, p2_v):
        py5.vertex(p1[0], p1[1])
        py5.vertex(p2[0], p2[1])
    py5.end_shape()
    
    # Draw the chaotic sphere as a faint glow
    py5.no_stroke()
    py5.fill(250, 100, 100, 20)
    py5.circle(cx, cy, r * 2)

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
