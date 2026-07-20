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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid Size
# Must be small enough to compute at 60fps, then we scale up for drawing
N = 120
ITER = 10 # Number of iterations for the Poisson solver (projection step)
dt = 0.1
diff = 0.0000
visc = 0.0000

# Grids: We have a velocity field (u, v) and a density field (d)
# We also track color fields for RGB dye
size = N + 2
u = np.zeros((size, size), dtype=np.float32)
v = np.zeros((size, size), dtype=np.float32)
u_prev = np.zeros((size, size), dtype=np.float32)
v_prev = np.zeros((size, size), dtype=np.float32)

dye_r = np.zeros((size, size), dtype=np.float32)
dye_g = np.zeros((size, size), dtype=np.float32)
dye_b = np.zeros((size, size), dtype=np.float32)
dye_r_prev = np.zeros((size, size), dtype=np.float32)
dye_g_prev = np.zeros((size, size), dtype=np.float32)
dye_b_prev = np.zeros((size, size), dtype=np.float32)

def set_bnd(b, x):
    # Boundary conditions
    x[0, :] = -x[1, :] if b == 1 else x[1, :]
    x[-1, :] = -x[-2, :] if b == 1 else x[-2, :]
    x[:, 0] = -x[:, 1] if b == 2 else x[:, 1]
    x[:, -1] = -x[:, -2] if b == 2 else x[:, -2]
    
    x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
    x[0, -1] = 0.5 * (x[1, -1] + x[0, -2])
    x[-1, 0] = 0.5 * (x[-2, 0] + x[-1, 1])
    x[-1, -1] = 0.5 * (x[-2, -1] + x[-1, -2])

def lin_solve(b, x, x0, a, c):
    # Solves linear system for diffusion and projection using Jacobi iteration
    for _ in range(ITER):
        x[1:-1, 1:-1] = (x0[1:-1, 1:-1] + a * (x[0:-2, 1:-1] + x[2:, 1:-1] + x[1:-1, 0:-2] + x[1:-1, 2:])) / c
        set_bnd(b, x)

def diffuse(b, x, x0, diff, dt):
    a = dt * diff * N * N
    lin_solve(b, x, x0, a, 1 + 4 * a)

def advect(b, d, d0, u, v, dt):
    dt0 = dt * N
    Y, X = np.ogrid[:size, :size]
    
    x = X - dt0 * u
    y = Y - dt0 * v
    
    x = np.clip(x, 0.5, N + 0.5)
    y = np.clip(y, 0.5, N + 0.5)
    
    i0 = x.astype(int)
    i1 = i0 + 1
    j0 = y.astype(int)
    j1 = j0 + 1
    
    s1 = x - i0
    s0 = 1.0 - s1
    t1 = y - j0
    t0 = 1.0 - t1
    
    d[1:-1, 1:-1] = (s0[1:-1, 1:-1] * (t0[1:-1, 1:-1] * d0[j0[1:-1, 1:-1], i0[1:-1, 1:-1]] + t1[1:-1, 1:-1] * d0[j1[1:-1, 1:-1], i0[1:-1, 1:-1]]) +
                     s1[1:-1, 1:-1] * (t0[1:-1, 1:-1] * d0[j0[1:-1, 1:-1], i1[1:-1, 1:-1]] + t1[1:-1, 1:-1] * d0[j1[1:-1, 1:-1], i1[1:-1, 1:-1]]))
    set_bnd(b, d)

def project(u, v, p, div):
    div[1:-1, 1:-1] = -0.5 * (u[1:-1, 2:] - u[1:-1, 0:-2] + v[2:, 1:-1] - v[0:-2, 1:-1]) / N
    p[...] = 0
    set_bnd(0, div)
    set_bnd(0, p)
    
    lin_solve(0, p, div, 1, 4)
    
    u[1:-1, 1:-1] -= 0.5 * N * (p[1:-1, 2:] - p[1:-1, 0:-2])
    v[1:-1, 1:-1] -= 0.5 * N * (p[2:, 1:-1] - p[0:-2, 1:-1])
    set_bnd(1, u)
    set_bnd(2, v)

def vel_step(u, v, u0, v0, dt):
    diffuse(1, u0, u, visc, dt)
    diffuse(2, v0, v, visc, dt)
    project(u0, v0, u, v)
    advect(1, u, u0, u0, v0, dt)
    advect(2, v, v0, u0, v0, dt)
    project(u, v, u0, v0)

def dens_step(x, x0, u, v, diff, dt):
    diffuse(0, x0, x, diff, dt)
    advect(0, x, x0, u, v, dt)

def add_source(x, s, dt):
    x += s * dt

def inject_dye_and_force(cx, cy, r, g, b, f_u, f_v):
    r_idx = int(cy * N)
    c_idx = int(cx * N)
    if 0 < r_idx < N and 0 < c_idx < N:
        dye_r_prev[r_idx, c_idx] = r
        dye_g_prev[r_idx, c_idx] = g
        dye_b_prev[r_idx, c_idx] = b
        u_prev[r_idx, c_idx] = f_u
        v_prev[r_idx, c_idx] = f_v

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.no_stroke()
    py5.background(0)

def draw():
    global u, v, u_prev, v_prev, dye_r, dye_g, dye_b, dye_r_prev, dye_g_prev, dye_b_prev
    
    # 1. Reset sources
    u_prev[...] = 0
    v_prev[...] = 0
    dye_r_prev[...] = 0
    dye_g_prev[...] = 0
    dye_b_prev[...] = 0
    
    # 2. Inject forces and dye dynamically using noise
    t = py5.frame_count * 0.01
    
    # Emitter 1: Neon Pink
    cx1 = 0.5 + py5.noise(t) * 0.4 - 0.2
    cy1 = 0.5 + py5.noise(t + 100) * 0.4 - 0.2
    fx1 = (py5.noise(t + 200) - 0.5) * 50
    fy1 = (py5.noise(t + 300) - 0.5) * 50
    inject_dye_and_force(cx1, cy1, 255, 20, 147, fx1, fy1)
    
    # Emitter 2: Cyan
    cx2 = 0.5 + py5.noise(t + 400) * 0.4 - 0.2
    cy2 = 0.5 + py5.noise(t + 500) * 0.4 - 0.2
    fx2 = (py5.noise(t + 600) - 0.5) * 50
    fy2 = (py5.noise(t + 700) - 0.5) * 50
    inject_dye_and_force(cx2, cy2, 0, 255, 255, fx2, fy2)
    
    # 3. Simulate Fluid Physics
    add_source(u, u_prev, dt)
    add_source(v, v_prev, dt)
    vel_step(u, v, u_prev, v_prev, dt)
    
    add_source(dye_r, dye_r_prev, dt)
    dens_step(dye_r, dye_r_prev, u, v, diff, dt)
    add_source(dye_g, dye_g_prev, dt)
    dens_step(dye_g, dye_g_prev, u, v, diff, dt)
    add_source(dye_b, dye_b_prev, dt)
    dens_step(dye_b, dye_b_prev, u, v, diff, dt)
    
    # Fade dye slightly over time
    dye_r *= 0.99
    dye_g *= 0.99
    dye_b *= 0.99
    
    # 4. Render Grid
    # We will map the N*N grid up to the screen size. Since N=120, this will be somewhat pixelated,
    # but drawing 14,400 rects is fast enough in py5.
    
    cell_w = py5.width / N
    cell_h = py5.height / N
    
    py5.background(0)
    
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            r = min(255, dye_r[j, i])
            g = min(255, dye_g[j, i])
            b = min(255, dye_b[j, i])
            
            if r > 5 or g > 5 or b > 5:
                py5.fill(r, g, b)
                py5.rect((i - 1) * cell_w, (j - 1) * cell_h, cell_w, cell_h)

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
