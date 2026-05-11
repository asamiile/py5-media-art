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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
N_STRINGS = 8
N_POINTS_PER_STRING = 40
N_PARTICLES = 160_000
STRING_RADIUS = 500

# State
strings = []
particles = None
particle_states = None  # [age, lifetime, string_idx, hue]
phase = 0


def setup():
    global strings, particles, particle_states
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Initialize strings
    for i in range(N_STRINGS):
        # random paths
        pts = np.random.uniform(-STRING_RADIUS, STRING_RADIUS, (N_POINTS_PER_STRING, 3))
        strings.append(pts)

    # Initialize particles
    particles = np.zeros((N_PARTICLES, 3), dtype=np.float32)
    particle_states = np.zeros((N_PARTICLES, 4), dtype=np.float32)
    # Reset all particles to "dead"
    particle_states[:, 0] = 1.0
    particle_states[:, 1] = 0.0


def draw():
    global strings, particles, particle_states, phase
    
    py5.background(0)
    phase += 0.05
    t = py5.frame_count / FPS
    
    # 1. Update Strings (Harmonic Vibration)
    updated_strings = []
    for pts in strings:
        # Add noise-based vibration
        noise = np.sin(pts[:, 0] * 0.01 + phase) * 10
        new_pts = pts.copy()
        new_pts[:, 2] += noise
        updated_strings.append(new_pts)

    # 2. Update Particles (Emission + Advection)
    # Emit new particles (faster)
    dead_mask = particle_states[:, 0] >= particle_states[:, 1]
    n_to_emit = min(np.sum(dead_mask), 1500)
    if n_to_emit > 0:
        dead_indices = np.where(dead_mask)[0][:n_to_emit]
        for idx in dead_indices:
            s_idx = np.random.randint(0, N_STRINGS)
            p_idx = np.random.randint(0, N_POINTS_PER_STRING)
            particles[idx] = updated_strings[s_idx][p_idx]
            particle_states[idx, 0] = 0
            particle_states[idx, 1] = np.random.uniform(40, 120)
            particle_states[idx, 2] = s_idx
            # Hues: 180 (Cyan), 280 (Violet), 320 (Magenta)
            hues = [180, 280, 320]
            particle_states[idx, 3] = hues[np.random.randint(0, 3)]

    # Advection
    alive_mask = particle_states[:, 0] < particle_states[:, 1]
    particles[alive_mask, 2] += 3.0 
    particles[alive_mask, 0] += np.sin(particles[alive_mask, 2] * 0.02 + phase) * 2.5
    particles[alive_mask, 1] += np.cos(particles[alive_mask, 2] * 0.02 + phase) * 2.5
    
    particle_states[alive_mask, 0] += 1.0

    # 3. Additive Background Stars
    py5.stroke_weight(1)
    for _ in range(40):
        sx = np.random.uniform(0, py5.width)
        sy = np.random.uniform(0, py5.height)
        py5.stroke(255, 255, 255, np.random.uniform(10, 60))
        py5.point(sx, sy)

    # 4. Projection
    cam_angle = t * 0.15
    c_ang, s_ang = np.cos(cam_angle), np.sin(cam_angle)
    
    def project(pts):
        px = pts[:, 0] * c_ang - pts[:, 2] * s_ang
        pz = pts[:, 0] * s_ang + pts[:, 2] * c_ang
        py = pts[:, 1]
        fov = 1200
        z_off = 1800
        s = fov / (pz + z_off)
        return px * s + py5.width / 2, py * s + py5.height / 2, s

    # 5. Render Particles
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    sx, sy, ss = project(particles)
    
    mask = alive_mask & (sx > 0) & (sx < py5.width) & (sy > 0) & (sy < py5.height)
    sx_m, sy_m, ss_m = sx[mask], sy[mask], ss[mask]
    hue_m = particle_states[mask, 3]
    life_ratio = particle_states[mask, 0] / particle_states[mask, 1]
    
    # Batch by hue and alpha buckets
    for h in [180, 280, 320]:
        h_mask = hue_m == h
        if np.any(h_mask):
            for a_idx in range(5):
                a_min = a_idx * 0.2
                a_max = (a_idx + 1) * 0.2
                alpha_mask = h_mask & (life_ratio >= a_min) & (life_ratio < a_max)
                if np.any(alpha_mask):
                    target_alpha = 25 * (1 - (a_min + 0.1))
                    py5.stroke(h, 60, 100, target_alpha)
                    py5.stroke_weight(1.5)
                    py5.points(np.stack([sx_m[alpha_mask], sy_m[alpha_mask]], axis=1))

    # 6. Render Strings (Smooth Threads)
    for pts in updated_strings:
        ssx, ssy, sss = project(pts)
        py5.no_fill()
        # Glow pass
        py5.stroke(0, 0, 100, 8)
        py5.stroke_weight(5)
        py5.begin_shape()
        for i in range(len(ssx)):
            py5.curve_vertex(ssx[i], ssy[i])
        py5.end_shape()
        # Core pass
        py5.stroke(0, 0, 100, 30)
        py5.stroke_weight(1.2)
        py5.begin_shape()
        for i in range(len(ssx)):
            py5.curve_vertex(ssx[i], ssy[i])
        py5.end_shape()

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


if __name__ == "__main__":
    py5.run_sketch()
