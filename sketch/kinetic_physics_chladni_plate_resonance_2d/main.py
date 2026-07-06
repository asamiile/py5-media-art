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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

N = 100_000
margin = 0

# Normalized coordinates [-1, 1]
pts = np.random.uniform(-1.0, 1.0, (N, 2))
vel = np.zeros_like(pts)

def chladni_grad(x, y, m, n):
    n_pi = n * np.pi
    m_pi = m * np.pi
    
    cos_nx = np.cos(n_pi * x)
    cos_ny = np.cos(n_pi * y)
    cos_mx = np.cos(m_pi * x)
    cos_my = np.cos(m_pi * y)
    
    sin_nx = np.sin(n_pi * x)
    sin_ny = np.sin(n_pi * y)
    sin_mx = np.sin(m_pi * x)
    sin_my = np.sin(m_pi * y)
    
    f = cos_nx * cos_my - cos_mx * cos_ny
    
    df_dx = -n_pi * sin_nx * cos_my + m_pi * sin_mx * cos_ny
    df_dy = -m_pi * cos_nx * sin_my + n_pi * cos_mx * sin_ny
    
    fx = -2 * f * df_dx
    fy = -2 * f * df_dy
    
    return np.column_stack((fx, fy))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 5)

def draw():
    global pts, vel
    
    py5.fill(10, 10, 5, 10) # 10% opacity for long trails
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    modes = [
        (1.0, 2.0),
        (3.0, 4.0),
        (5.0, 2.0),
        (4.0, 4.0),
        (6.0, 3.0),
        (7.0, 4.0),
        (1.0, 2.0)
    ]
    
    mode_idx = t * (len(modes) - 1)
    idx0 = int(mode_idx)
    idx1 = min(idx0 + 1, len(modes) - 1)
    frac = mode_idx - idx0
    
    # Smoothstep interpolation
    frac = frac * frac * (3 - 2 * frac)
    
    m0, n0 = modes[idx0]
    m1, n1 = modes[idx1]
    
    m = m0 + (m1 - m0) * frac
    n = n0 + (n1 - n0) * frac
    
    force = chladni_grad(pts[:, 0], pts[:, 1], m, n)
    
    noise = np.random.randn(N, 2) * 0.001
    
    # Drastically reduce force coefficient so they gather slowly
    vel = vel * 0.8 + force * 0.002 + noise
    pts += vel * 0.02
    
    hit_x = np.abs(pts[:, 0]) > 1.0
    pts[hit_x, 0] = np.sign(pts[hit_x, 0]) * 1.0
    vel[hit_x, 0] *= -0.5
    
    hit_y = np.abs(pts[:, 1]) > 1.0
    pts[hit_y, 1] = np.sign(pts[hit_y, 1]) * 1.0
    vel[hit_y, 1] *= -0.5

    # Draw
    screen_pts = (pts + 1.0) * 0.5 * np.array([SIZE[0], SIZE[1]])
    
    py5.stroke(45, 80, 100, 30)
    py5.stroke_weight(2.0)
    py5.points(screen_pts)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
