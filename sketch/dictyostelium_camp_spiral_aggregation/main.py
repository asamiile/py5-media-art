from pathlib import Path
import shutil
import subprocess
import sys
import random
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

# Animation Settings
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation settings
NUM_CELLS = 1800
pos = np.zeros((NUM_CELLS, 3), dtype=np.float32)
vel = np.zeros((NUM_CELLS, 3), dtype=np.float32)
cell_sizes = np.zeros(NUM_CELLS, dtype=np.float32)


# Two spiral centers (cAMP source nodes)
centers = np.array([
    [-300.0, -150.0, 0.0],
    [300.0, 150.0, 0.0]
], dtype=np.float32)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    global pos, vel, cell_sizes
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize cells in a wide, flat disk
    for i in range(NUM_CELLS):
        r = random.uniform(50, 1200)
        theta = random.uniform(0, py5.TWO_PI)
        pos[i, 0] = r * np.cos(theta)
        pos[i, 1] = r * np.sin(theta)
        pos[i, 2] = random.uniform(-100, 100)

        cell_sizes[i] = random.uniform(3.0, 7.0)



def draw():
    global pos, vel

    # Reset blend mode for background draw to avoid cumulative additive color build-up
    py5.blend_mode(py5.BLEND)
    # Deep slate-charcoal background with trailing motion blur
    py5.fill(17, 18, 21, 35)
    py5.rect(0, 0, *SIZE)

    py5.blend_mode(py5.ADD)

    # Camera rotation angles over time
    angle_y = py5.frame_count * 0.003
    angle_x = 0.4 + 0.1 * np.sin(py5.frame_count * 0.005)
    cos_y, sin_y = np.cos(angle_y), np.sin(angle_y)
    cos_x, sin_x = np.cos(angle_x), np.sin(angle_x)

    # 1. Draw cAMP spiral waves as faint background particles/structures
    # Generating a mathematical representation of the spiral fields
    z_cam = 1500.0
    fov = 1300.0
    py5.no_fill()
    py5.stroke_weight(1)

    # Faint spiral field dots in background
    for c_idx, center in enumerate(centers):
        # Rotate center position
        cx = center[0] * cos_y - center[2] * sin_y
        cz = center[0] * sin_y + center[2] * cos_y
        cy = center[1] * cos_x - cz * sin_x
        cz2 = center[1] * sin_x + cz * cos_x
        cpz = cz2 + z_cam

        if cpz > 50.0:
            csx = cx / cpz * fov + SIZE[0] / 2
            csy = cy / cpz * fov + SIZE[1] / 2

            # Draw glowing core
            py5.stroke(255, 20, 147, 50)
            py5.stroke_weight(25)
            py5.point(csx, csy)
            py5.stroke(255, 255, 255, 120)
            py5.stroke_weight(6)
            py5.point(csx, csy)

    # Update cell physics (Chemotaxis along cAMP spirals + cohesion)
    # Find nearest center for each particle
    diffs = pos[:, None, :] - centers[None, :, :]  # Shape: (NUM_CELLS, 2, 3)
    dists = np.linalg.norm(diffs, axis=2)          # Shape: (NUM_CELLS, 2)
    nearest_center_idx = np.argmin(dists, axis=1)  # Shape: (NUM_CELLS)

    # Gather parameters relative to nearest center
    target_centers = centers[nearest_center_idx]
    rel_pos = pos - target_centers
    r_dists = dists[np.arange(NUM_CELLS), nearest_center_idx]
    r_dists = np.maximum(r_dists, 1.0)

    # Radial direction towards center
    dir_to_center = -rel_pos / r_dists[:, None]

    # Tangential direction (spiral twist direction)
    tangential = np.zeros_like(rel_pos)
    tangential[:, 0] = -rel_pos[:, 1]
    tangential[:, 1] = rel_pos[:, 0]
    t_norms = np.linalg.norm(tangential, axis=1)
    t_norms = np.maximum(t_norms, 1.0)
    tangential /= t_norms[:, None]

    # Angle to center
    thetas = np.arctan2(rel_pos[:, 1], rel_pos[:, 0])

    # cAMP wave phase: wave travels outwards. peak is where phase is near 0/TWO_PI
    # Wave speed and frequency parameters
    wave_freq = 0.015
    wave_speed = 0.05
    phases = (r_dists * wave_freq - thetas + py5.frame_count * wave_speed) % py5.TWO_PI

    # Chemotaxis force: Cells seek wavefront peaks (phase = 0) and drift inwards
    # Force direction is a blend of radial attraction and tangential flow along the wavefront
    chemotaxis_strength = 2.8 * (1.0 + np.sin(phases))
    attraction_force = dir_to_center * 1.5 + tangential * 0.8
    chemotaxis = attraction_force * chemotaxis_strength[:, None]

    # Cell-cell cohesion (local aggregation into streams)
    # To keep it fast, compute cohesion on a subset or downsampled neighborhood
    cohesion = np.zeros_like(pos)
    # NumPy vectorized batch calculation for local neighbors
    # Chunking to avoid huge memory footprint: compare each particle with 80 random other particles
    sample_indices = np.random.randint(0, NUM_CELLS, size=(NUM_CELLS, 80))
    for k in range(80):
        neighbor_pos = pos[sample_indices[:, k]]
        n_diff = neighbor_pos - pos
        n_dist = np.linalg.norm(n_diff, axis=1)
        n_dist = np.maximum(n_dist, 1.0)
        # Only cohere if close (threshold: 90px)
        mask = (n_dist < 90.0) & (n_dist > 5.0)
        weight = (90.0 - n_dist) / 90.0
        cohesion[mask] += (n_diff[mask] / n_dist[mask, None]) * weight[mask, None] * 0.12

    # Brownian random drift
    random_drift = np.random.normal(0, 0.4, size=pos.shape).astype(np.float32)

    # Update cells velocity & position
    vel = vel * 0.88 + (chemotaxis + cohesion + random_drift) * 0.12
    pos += vel

    # Rotate all cell positions for rendering
    rot_pos = np.zeros_like(pos)
    rot_pos[:, 0] = pos[:, 0] * cos_y - pos[:, 2] * sin_y
    z_temp = pos[:, 0] * sin_y + pos[:, 2] * cos_y
    rot_pos[:, 1] = pos[:, 1] * cos_x - z_temp * sin_x
    rot_pos[:, 2] = pos[:, 1] * sin_x + z_temp * cos_x

    # Depth sorting (Painter's Algorithm)
    z_depths = rot_pos[:, 2] + z_cam
    sort_indices = np.argsort(-z_depths)

    # Draw cells
    for idx in sort_indices:
        pz = z_depths[idx]
        if pz < 50.0:
            continue

        sx = rot_pos[idx, 0] / pz * fov + SIZE[0] / 2
        sy = rot_pos[idx, 1] / pz * fov + SIZE[1] / 2

        # Scale size and opacity by depth
        fade = 1.0 - (pz - 600.0) / 1800.0
        fade = max(0.1, min(1.2, fade))

        proj_size = cell_sizes[idx] * fov / pz

        # Cell color depends on its distance to nearest center (glowing amber near cores)
        dist_to_core = r_dists[idx]
        if dist_to_core < 180.0:
            # Hot white-yellow core
            py5.stroke(255, 255, 255, int(230 * fade))
            py5.stroke_weight(proj_size * 1.5)
            py5.point(sx, sy)

            py5.stroke(255, 170, 29, int(180 * fade))
            py5.stroke_weight(proj_size * 3.5)
            py5.point(sx, sy)
        else:
            # Amber cells forming streams along cAMP wave
            p_val = phases[idx]
            # Saturated amber peak
            r_val = int(255 * fade)
            g_val = int((140 + 70 * np.sin(p_val)) * fade)
            b_val = int(30 * fade)

            py5.stroke(r_val, g_val, b_val, int(150 * fade))
            py5.stroke_weight(proj_size * 1.8)
            py5.point(sx, sy)

            py5.stroke(255, 20, 147, int(60 * fade * np.sin(p_val)))
            py5.stroke_weight(proj_size * 3.0)
            py5.point(sx, sy)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
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

        import os
        os._exit(0)


py5.run_sketch()
