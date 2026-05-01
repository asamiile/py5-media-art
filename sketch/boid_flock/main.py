from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, render_video_and_preview, save_animation_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = frames_dir(SKETCH_DIR)
DURATION_SEC = 8
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 480

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()
W, H = SIZE

N = 300         # number of boids
MAX_SPEED = 4.0
MIN_SPEED = 1.8

SEP_R = 22     # separation radius
ALI_R = 55     # alignment radius
COH_R = 75     # cohesion radius
SEP_W = 2.0    # separation weight
ALI_W = 1.0    # alignment weight
COH_W = 0.7    # cohesion weight

TRAIL = 50     # trail length in frames

pos = None      # (N, 2) float32
vel = None      # (N, 2) float32
history = None  # (TRAIL, N, 2) float32 circular buffer
ptr = 0         # write pointer into history


def _hsv_batch(hues_deg, s=0.88, v=1.0):
    h = hues_deg / 60.0
    ii = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p = np.full_like(hues_deg, v * (1 - s))
    q = v * (1 - s * f)
    tv = v * (1 - s * (1 - f))
    vv = np.full_like(hues_deg, v)
    cnd = [ii == k for k in range(6)]
    r = (np.select(cnd, [vv, q, p, p, tv, vv]) * 255).astype(int)
    g = (np.select(cnd, [tv, vv, vv, q, p, p]) * 255).astype(int)
    b = (np.select(cnd, [p, p, tv, vv, vv, q]) * 255).astype(int)
    return r, g, b


def _step():
    global pos, vel
    # Pairwise displacements: diff[i,j] = pos[i] - pos[j]  (from j toward i)
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]   # (N, N, 2)
    dist = np.sqrt((diff ** 2).sum(axis=-1)) + 1e-8        # (N, N)

    sep_m = (dist < SEP_R) & (dist > 0.01)
    ali_m = (dist < ALI_R) & (dist > 0.01)
    coh_m = (dist < COH_R) & (dist > 0.01)

    # Separation: steer away from close neighbors (average displacement toward i)
    cnt = sep_m.sum(axis=1, keepdims=True).clip(min=1)
    sep_f = (diff * sep_m[:, :, np.newaxis]).sum(axis=1) / cnt

    # Alignment: match average velocity of alignment neighbors
    cnt = ali_m.sum(axis=1, keepdims=True).clip(min=1)
    ali_f = (vel[np.newaxis] * ali_m[:, :, np.newaxis]).sum(axis=1) / cnt

    # Cohesion: steer toward centroid of cohesion neighbors
    cnt = coh_m.sum(axis=1, keepdims=True).clip(min=1)
    center = (pos[np.newaxis] * coh_m[:, :, np.newaxis]).sum(axis=1) / cnt
    coh_f = center - pos

    def norm(f):
        mag = np.sqrt((f ** 2).sum(axis=-1, keepdims=True)) + 1e-8
        return f / mag

    vel = vel + SEP_W * norm(sep_f) + ALI_W * norm(ali_f) + COH_W * norm(coh_f)

    speed = np.sqrt((vel ** 2).sum(axis=-1, keepdims=True)) + 1e-8
    vel = np.where(speed > MAX_SPEED, vel / speed * MAX_SPEED, vel)
    vel = np.where(speed < MIN_SPEED, vel / speed * MIN_SPEED, vel)

    pos = (pos + vel) % np.array([W, H], dtype=np.float32)


def setup():
    global pos, vel, history
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)

    pos = np.random.uniform([0, 0], [W, H], (N, 2)).astype(np.float32)
    angles = np.random.uniform(0, 2 * np.pi, N).astype(np.float32)
    speeds = np.random.uniform(MIN_SPEED, MAX_SPEED, N).astype(np.float32)
    vel = np.stack([speeds * np.cos(angles), speeds * np.sin(angles)], axis=-1)

    history = np.tile(pos[np.newaxis], (TRAIL, 1, 1))

    py5.background(4, 6, 18)


def draw():
    global ptr

    # Update physics
    _step()

    # Store current positions in circular buffer
    history[ptr] = pos
    ptr = (ptr + 1) % TRAIL

    # Dark background (partial fade for glow accumulation)
    py5.background(4, 6, 18)

    # Boid colors by heading angle
    headings = np.arctan2(vel[:, 1], vel[:, 0])      # -π to π
    hues = (np.degrees(headings) + 180.0) % 360.0    # 0→360
    rs, gs, bs = _hsv_batch(hues)

    # Draw trails oldest→newest
    idx_order = [(ptr + t) % TRAIL for t in range(TRAIL)]
    traj = history[idx_order]  # (TRAIL, N, 2): traj[0]=oldest … traj[-1]=newest

    py5.stroke_weight(1.6)
    for t in range(1, TRAIL):
        alpha = int(t / TRAIL * 210)
        p0 = traj[t - 1]   # (N, 2) previous positions
        p1 = traj[t]        # (N, 2) current positions

        # Skip segments that cross a wrap boundary
        dx = np.abs(p1[:, 0] - p0[:, 0])
        dy = np.abs(p1[:, 1] - p0[:, 1])
        valid = (dx < W / 2) & (dy < H / 2)

        for i in range(N):
            if not valid[i]:
                continue
            py5.stroke(int(rs[i]), int(gs[i]), int(bs[i]), alpha)
            py5.line(float(p0[i, 0]), float(p0[i, 1]), float(p1[i, 0]), float(p1[i, 1]))

    save_animation_frame(FRAMES_DIR)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_frame=TOTAL_FRAMES // 2,
        )


py5.run_sketch()
