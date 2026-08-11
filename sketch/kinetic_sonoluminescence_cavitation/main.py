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

# Particle & Field state
NUM_BUBBLES = 1200
pos = np.zeros((NUM_BUBBLES, 3), dtype=np.float32)
vel = np.zeros((NUM_BUBBLES, 3), dtype=np.float32)
base_r = np.zeros(NUM_BUBBLES, dtype=np.float32)
phases = np.zeros(NUM_BUBBLES, dtype=np.float32)
flash_intensity = np.zeros(NUM_BUBBLES, dtype=np.float32)

# Shockwaves list (Expanding spheres): [{"pos": [x,y,z], "radius": r, "max_radius": mr, "alpha": a}]
shockwaves = []


def setup():
    global pos, vel, base_r, phases
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize bubbles in a spherical cloud around the center
    for i in range(NUM_BUBBLES):
        r = random.uniform(200, 1000)
        theta = random.uniform(0, py5.TWO_PI)
        phi = random.uniform(0, py5.PI)

        pos[i, 0] = r * np.sin(phi) * np.cos(theta)
        pos[i, 1] = r * np.sin(phi) * np.sin(theta)
        pos[i, 2] = r * np.cos(phi)

        base_r[i] = random.uniform(6.0, 16.0)
        phases[i] = random.uniform(0, py5.TWO_PI)


def draw():
    global pos, vel, flash_intensity, shockwaves

    # Deep indigo background with low opacity for slight motion blur trailing
    py5.fill(3, 1, 11, 40)
    py5.rect(0, 0, *SIZE)

    py5.blend_mode(py5.ADD)

    # Camera rotation angles over time
    angle_y = py5.frame_count * 0.005
    angle_x = py5.frame_count * 0.003
    cos_y, sin_y = np.cos(angle_y), np.sin(angle_y)
    cos_x, sin_x = np.cos(angle_x), np.sin(angle_x)

    # Draw acoustic standing wave pressure fields (rendered mathematically as projected rings)
    # Drawing concentric 3D circles projected onto 2D
    py5.no_fill()
    for i in range(1, 5):
        wave_pulse = np.sin(py5.frame_count * 0.05 - i * 0.8)
        radius = i * 280 + wave_pulse * 30

        # Draw circle on XZ plane
        for theta in np.linspace(0, py5.TWO_PI, 100):
            cx = radius * np.cos(theta)
            cz = radius * np.sin(theta)
            cy = 0.0

            # Rotate
            rx = cx * cos_y - cz * sin_y
            rz = cx * sin_y + cz * cos_y
            ry = cy * cos_x - rz * sin_x
            rz2 = cy * sin_x + rz * cos_x

            # Project
            z_cam = 1600.0
            proj_z = rz2 + z_cam
            if proj_z > 50.0:
                fov = 1500.0
                sx = rx / proj_z * fov + SIZE[0] / 2
                sy = ry / proj_z * fov + SIZE[1] / 2
                alpha = int((15 + 10 * wave_pulse) * (1.0 - (proj_z - 800.0) / 1600.0))
                alpha = max(0, min(255, alpha))
                py5.stroke(24, 28, 90, alpha)
                py5.stroke_weight(2)
                py5.point(sx, sy)

    # Update Physics
    for i in range(NUM_BUBBLES):
        to_center = -pos[i]
        dist = np.linalg.norm(to_center)
        dist = max(dist, 1.0)
        direction = to_center / dist

        # Acoustic pressure force driving bubbles toward center
        pressure_gradient = np.sin(dist * 0.01 - py5.frame_count * 0.08)
        attraction = direction * (4.0 + 3.0 * pressure_gradient)

        # Noise turbulence
        n_val = py5.noise(pos[i, 0] * 0.005, pos[i, 1] * 0.005, py5.frame_count * 0.01)
        turbulence = np.array([
            np.cos(n_val * py5.TWO_PI),
            np.sin(n_val * py5.TWO_PI),
            np.sin(n_val * py5.PI)
        ], dtype=np.float32) * 1.5

        # Update physics
        vel[i] = vel[i] * 0.94 + (attraction + turbulence) * 0.06
        pos[i] += vel[i]

        # Sonoluminescence collapse dynamics
        t = (py5.frame_count * 0.12 + phases[i]) % py5.TWO_PI
        if t < 5.0:
            r_scale = 1.0 + 0.8 * (t / 5.0)
        else:
            collapse_frac = (py5.TWO_PI - t) / (py5.TWO_PI - 5.0)
            r_scale = 0.05 + 1.75 * (collapse_frac ** 4)

            # Emit flash at peak collapse near center
            if collapse_frac < 0.05 and dist < 450:
                flash_intensity[i] = 1.0
                if len(shockwaves) < 20 and random.random() < 0.06:
                    shockwaves.append({
                        "pos": pos[i].copy(),
                        "radius": 10.0,
                        "max_radius": random.uniform(200, 500),
                        "alpha": 255.0
                    })

        flash_intensity[i] *= 0.85

    # Rotate all bubble positions for rendering
    rot_pos = np.zeros_like(pos)
    rot_pos[:, 0] = pos[:, 0] * cos_y - pos[:, 2] * sin_y
    z_temp = pos[:, 0] * sin_y + pos[:, 2] * cos_y
    rot_pos[:, 1] = pos[:, 1] * cos_x - z_temp * sin_x
    rot_pos[:, 2] = pos[:, 1] * sin_x + z_temp * cos_x

    # Depth sorting (Painter's Algorithm)
    z_cam = 1600.0
    z_depths = rot_pos[:, 2] + z_cam
    sort_indices = np.argsort(-z_depths)  # Back to front

    # Render Bubbles
    fov = 1500.0
    for idx in sort_indices:
        pz = z_depths[idx]
        if pz < 50.0:
            continue

        # 3D to 2D Projection
        sx = rot_pos[idx, 0] / pz * fov + SIZE[0] / 2
        sy = rot_pos[idx, 1] / pz * fov + SIZE[1] / 2

        # Draw size scaling by depth
        t = (py5.frame_count * 0.12 + phases[idx]) % py5.TWO_PI
        if t < 5.0:
            r_scale = 1.0 + 0.8 * (t / 5.0)
        else:
            collapse_frac = (py5.TWO_PI - t) / (py5.TWO_PI - 5.0)
            r_scale = 0.05 + 1.75 * (collapse_frac ** 4)

        current_r = base_r[idx] * r_scale
        proj_size = current_r * fov / pz

        # Depth fade factor
        fade = 1.0 - (pz - 600.0) / 1800.0
        fade = max(0.1, min(1.2, fade))

        if flash_intensity[idx] > 0.05:
            # Hot spot flash
            py5.stroke(255, 255, 255, int(flash_intensity[idx] * 255 * fade))
            py5.stroke_weight(proj_size * 2.5)
            py5.point(sx, sy)

            py5.stroke(0, 240, 255, int(flash_intensity[idx] * 180 * fade))
            py5.stroke_weight(proj_size * 5.0)
            py5.point(sx, sy)
        else:
            # Normal bubble
            py5.stroke(35, 39, 122, int(90 * fade))
            py5.stroke_weight(proj_size * 1.5)
            py5.point(sx, sy)

            py5.stroke(0, 240, 255, int(160 * fade))
            py5.stroke_weight(proj_size * 0.5)
            py5.point(sx, sy)

    # Update and draw shockwaves (using 3D projection)
    next_shockwaves = []
    for sw in shockwaves:
        sw["radius"] += 8.0
        sw["alpha"] *= 0.94
        if sw["alpha"] > 2.0 and sw["radius"] < sw["max_radius"]:
            # Render a projected circle outline for the shockwave sphere
            num_points = 64
            points_x = []
            points_y = []
            for angle in np.linspace(0, py5.TWO_PI, num_points):
                # Calculate circle on local billboard plane (facing camera)
                bx = sw["radius"] * np.cos(angle)
                by = sw["radius"] * np.sin(angle)
                bz = 0.0

                # World coordinates
                wx = sw["pos"][0] + bx
                wy = sw["pos"][1] + by
                wz = sw["pos"][2] + bz

                # Rotate
                rx = wx * cos_y - wz * sin_y
                rz = wx * sin_y + wz * cos_y
                ry = wy * cos_x - rz * sin_x
                rz2 = wy * sin_x + rz * cos_x

                pz = rz2 + z_cam
                if pz > 50.0:
                    sx = rx / pz * fov + SIZE[0] / 2
                    sy = ry / pz * fov + SIZE[1] / 2
                    points_x.append(sx)
                    points_y.append(sy)

            if len(points_x) > 2:
                py5.stroke(0, 240, 255, int(sw["alpha"] * 0.4))
                py5.stroke_weight(3)
                py5.begin_shape()
                for px, py_val in zip(points_x, points_y):
                    py5.vertex(px, py_val)
                py5.end_shape(py5.CLOSE)

            next_shockwaves.append(sw)
    shockwaves = next_shockwaves

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
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
