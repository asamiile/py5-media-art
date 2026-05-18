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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# DLA Parameters
N_IONS = 150_000
STEPS_PER_FRAME = 8
DRIFT_SPEED = 0.25
RANDOM_WALK_SCALE = 2.0

grid_w, grid_h = SIZE
cx, cy = grid_w // 2, grid_h // 2

grid = np.zeros((grid_h, grid_w), dtype=bool)
buffer = np.full((grid_h, grid_w, 4), [255, 10, 10, 15], dtype=np.uint8)

# Initial core
grid[cy-5:cy+5, cx-5:cx+5] = True
buffer[cy-5:cy+5, cx-5:cx+5] = [255, 255, 150, 80]

ions_pos = np.zeros((N_IONS, 2), dtype=np.float32)
max_radius = 15.0

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial spawn
    theta = np.random.uniform(0, 2*np.pi, N_IONS)
    r = np.random.uniform(50, grid_h/2, N_IONS)
    ions_pos[:, 0] = cx + r * np.cos(theta)
    ions_pos[:, 1] = cy + r * np.sin(theta)

def draw():
    global max_radius, ions_pos, grid, buffer
    
    for _ in range(STEPS_PER_FRAME):
        # Random walk
        ions_pos += np.random.randn(N_IONS, 2).astype(np.float32) * RANDOM_WALK_SCALE
        
        # Drift towards center
        dx = cx - ions_pos[:, 0]
        dy = cy - ions_pos[:, 1]
        dist = np.hypot(dx, dy) + 1e-5
        
        ions_pos[:, 0] += (dx / dist) * DRIFT_SPEED
        ions_pos[:, 1] += (dy / dist) * DRIFT_SPEED
        
        # Clip to bounds
        np.clip(ions_pos[:, 0], 2, grid_w-3, out=ions_pos[:, 0])
        np.clip(ions_pos[:, 1], 2, grid_h-3, out=ions_pos[:, 1])
        
        ix = ions_pos[:, 0].astype(np.int32)
        iy = ions_pos[:, 1].astype(np.int32)
        
        # 8-way neighbor check
        touch = (grid[iy, ix+1] | grid[iy, ix-1] | grid[iy+1, ix] | grid[iy-1, ix] |
                 grid[iy+1, ix+1] | grid[iy-1, ix-1] | grid[iy+1, ix-1] | grid[iy-1, ix+1])
        
        if np.any(touch):
            t_ix = ix[touch]
            t_iy = iy[touch]
            n_touch = len(t_ix)
            
            # Update max radius
            dists = np.hypot(t_ix - cx, t_iy - cy)
            current_max = np.max(dists)
            if current_max > max_radius:
                max_radius = float(current_max)
            
            # Colors based on age
            age_ratio = min(1.0, py5.frame_count / TOTAL_FRAMES)
            r_base = np.interp(age_ratio, [0, 0.5, 1], [255, 200, 240])
            g_base = np.interp(age_ratio, [0, 0.5, 1], [150, 230, 255])
            b_base = np.interp(age_ratio, [0, 0.5, 1], [80, 255, 255])
            
            brightness = np.random.uniform(0.7, 1.4, n_touch)
            # Ensure colors are within bounds and have shape (n_touch, 4)
            c = np.column_stack((
                np.full(n_touch, 255, dtype=np.uint8),
                np.clip(r_base * brightness, 0, 255).astype(np.uint8),
                np.clip(g_base * brightness, 0, 255).astype(np.uint8),
                np.clip(b_base * brightness, 0, 255).astype(np.uint8)
            ))
            
            # Splat 2x2 for thickness
            for dx_splat in [0, 1]:
                for dy_splat in [0, 1]:
                    nx = t_ix + dx_splat
                    ny = t_iy + dy_splat
                    valid = (ny >= 0) & (ny < grid_h) & (nx >= 0) & (nx < grid_w)
                    vy = ny[valid]
                    vx = nx[valid]
                    
                    grid[vy, vx] = True
                    buffer[vy, vx] = c[valid]
            
            # Respawn stuck ions outside the current max radius
            spawn_r = min(max_radius + 150, float(grid_w))
            theta = np.random.uniform(0, 2*np.pi, n_touch)
            ions_pos[touch, 0] = cx + spawn_r * np.cos(theta)
            ions_pos[touch, 1] = cy + spawn_r * np.sin(theta)

    # Render aggregate
    py5.load_np_pixels()
    py5.np_pixels[:] = buffer
    py5.update_np_pixels()
    
    # Render moving ions (Electric Blue)
    py5.blend_mode(py5.ADD)
    py5.stroke(50, 150, 255, 25)
    py5.stroke_weight(2)
    py5.points(ions_pos)
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
