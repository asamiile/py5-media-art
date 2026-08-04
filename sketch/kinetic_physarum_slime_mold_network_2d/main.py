"""
kinetic_physarum_slime_mold_network_2d

A 4K kinetic visualization of Jeff Jones' agent-based Physarum polycephalum
(slime mold) simulation. 80,000 autonomous agents split into 3 distinct
species drift and sense chemical trail gradients, self-organizing into an
intricate organic network. The colony actively bridges 6 orbiting food sources,
dynamically rewiring its bioluminescent trail highways over time.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import math
import numpy as np

import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840x2160

# --- Simulation dimensions ---
SIM_W = 1280
SIM_H = 720
N = 80000

# --- State ---
pos = None       # Agent positions (N, 2)
ang = None       # Agent angles (N,)
species = None   # Agent species ID (N,)
trail = None     # Shared trail grid (SIM_H, SIM_W)
pimg = None      # Offscreen Py5Image for blit
lut_rgb = None   # Color lookup table for trails

# Species parameters (heterogeneous behavior)
sensor_dist = None
sensor_angle = None
turn_angle = None
speed = None

# Color palettes for the three species (additive overlay colors)
# Species 0: Teal/Mint
# Species 1: Solar Gold/Amber
# Species 2: Fuchsia/Magenta
SPECIES_COLORS = [
    np.array([10, 220, 200], dtype=np.float32),  # Teal
    np.array([255, 170, 10], dtype=np.float32),  # Gold
    np.array([240, 20, 150], dtype=np.float32),  # Magenta
]


def make_color_lut():
    """Create a high-fidelity 256-color RGB lookup table for trails."""
    # Palette transition:
    # 0: #010103 (dark void)
    # 128: #002A32 (deep forest teal)
    # 220: #3DFFB5 (bioluminescent mint)
    # 255: #FFD23F (solar amber gold)
    lut = np.zeros((256, 3), dtype=np.float32)
    for i in range(129):
        t = i / 128.0
        lut[i] = (1 - t) * np.array([1, 1, 3]) + t * np.array([0, 42, 50])
    for i in range(129, 221):
        t = (i - 128) / (220.0 - 128.0)
        lut[i] = (1 - t) * np.array([0, 42, 50]) + t * np.array([61, 255, 181])
    for i in range(221, 256):
        t = (i - 220) / (255.0 - 220.0)
        lut[i] = (1 - t) * np.array([61, 255, 181]) + t * np.array([255, 210, 63])
    return np.clip(lut, 0, 255).astype(np.float32)


def setup():
    global pos, ang, species, trail, pimg, lut_rgb
    global sensor_dist, sensor_angle, turn_angle, speed

    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

    rng = np.random.default_rng(None)

    # Initialize positions and orientations
    # Distribute them in a loose circle around the center
    r_init = rng.uniform(0, SIM_H * 0.45, N)
    theta_init = rng.uniform(0, 2 * np.pi, N)
    pos = np.zeros((N, 2), dtype=np.float32)
    pos[:, 0] = SIM_W / 2 + r_init * np.cos(theta_init)
    pos[:, 1] = SIM_H / 2 + r_init * np.sin(theta_init)
    ang = rng.uniform(0, 2 * np.pi, N).astype(np.float32)

    # Species grouping
    species = np.arange(N) % 3

    # Define heterogeneous species parameters
    sd_vals = np.array([12.0, 18.0, 14.0], dtype=np.float32)
    sa_vals = np.array([22.5, 45.0, 30.0], dtype=np.float32) * (np.pi / 180.0)
    ta_vals = np.array([22.5, 45.0, 15.0], dtype=np.float32) * (np.pi / 180.0)
    sp_vals = np.array([2.2, 1.6, 2.8], dtype=np.float32)

    sensor_dist = sd_vals[species]
    sensor_angle = sa_vals[species]
    turn_angle = ta_vals[species]
    speed = sp_vals[species]

    # Shared trail grid
    trail = np.zeros((SIM_H, SIM_W), dtype=np.float32)

    # Offscreen image buffer for blitting
    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)

    # Precompute LUT
    lut_rgb = make_color_lut()


def update_physarum(t):
    global trail
    rng = np.random.default_rng()

    # --- 1. Sense ---
    cos_c, sin_c = np.cos(ang), np.sin(ang)
    cos_l, sin_l = np.cos(ang - sensor_angle), np.sin(ang - sensor_angle)
    cos_r, sin_r = np.cos(ang + sensor_angle), np.sin(ang + sensor_angle)

    sx_c = (pos[:, 0] + cos_c * sensor_dist).astype(np.int32) % SIM_W
    sy_c = (pos[:, 1] + sin_c * sensor_dist).astype(np.int32) % SIM_H

    sx_l = (pos[:, 0] + cos_l * sensor_dist).astype(np.int32) % SIM_W
    sy_l = (pos[:, 1] + sin_l * sensor_dist).astype(np.int32) % SIM_H

    sx_r = (pos[:, 0] + cos_r * sensor_dist).astype(np.int32) % SIM_W
    sy_r = (pos[:, 1] + sin_r * sensor_dist).astype(np.int32) % SIM_H

    val_c = trail[sy_c, sx_c]
    val_l = trail[sy_l, sx_l]
    val_r = trail[sy_r, sx_r]

    # Steering logic
    turn = np.zeros(N, dtype=np.float32)

    # Left best -> turn left
    left_best = (val_l > val_c) & (val_l > val_r)
    turn[left_best] -= turn_angle[left_best]

    # Right best -> turn right
    right_best = (val_r > val_c) & (val_r > val_l)
    turn[right_best] += turn_angle[right_best]

    # Both best -> choose direction randomly
    both_best = (val_l > val_c) & (val_r > val_c) & ~left_best & ~right_best
    rand_dirs = rng.choice([-1.0, 1.0], size=N).astype(np.float32)
    turn[both_best] += rand_dirs[both_best] * turn_angle[both_best]

    # Add small directional wobble
    wobble = rng.normal(0, 0.1, N).astype(np.float32)
    ang[:] += turn + wobble

    # --- 2. Move ---
    pos[:, 0] += np.cos(ang) * speed
    pos[:, 1] += np.sin(ang) * speed
    pos[:, 0] %= SIM_W
    pos[:, 1] %= SIM_H

    # --- 3. Deposit ---
    ix = pos[:, 0].astype(np.int32)
    iy = pos[:, 1].astype(np.int32)
    # Deposit pheromones
    np.add.at(trail, (iy, ix), 12.0)

    # Inject food attractors (constantly write high values)
    # Orbiting food positions (6 points)
    num_foods = 6
    for i in range(num_foods):
        angle = t * np.pi * 2 + i * (np.pi * 2 / num_foods)
        r = (SIM_H * 0.38) * (1.0 + 0.12 * math.sin(t * np.pi * 4 + i))
        fx = SIM_W / 2 + r * math.cos(angle)
        fy = SIM_H / 2 + r * math.sin(angle)
        
        # Write soft gaussian stamp
        f_ix = int(fx) % SIM_W
        f_iy = int(fy) % SIM_H
        for dy in [-2, -1, 0, 1, 2]:
            for dx in [-2, -1, 0, 1, 2]:
                px = (f_ix + dx) % SIM_W
                py_v = (f_iy + dy) % SIM_H
                dist_sq = dx*dx + dy*dy
                stamp = max(0, 255 - dist_sq * 30)
                trail[py_v, px] = max(trail[py_v, px], stamp)

    # Clamp trail values
    np.clip(trail, 0, 255, out=trail)

    # --- 4. Diffuse & Evaporate ---
    blur = (
        trail
        + np.roll(trail, 1, 0) + np.roll(trail, -1, 0)
        + np.roll(trail, 1, 1) + np.roll(trail, -1, 1)
        + np.roll(np.roll(trail, 1, 0), 1, 1)
        + np.roll(np.roll(trail, 1, 0), -1, 1)
        + np.roll(np.roll(trail, -1, 0), 1, 1)
        + np.roll(np.roll(trail, -1, 0), -1, 1)
    ) / 9.0
    # Slow decay rate for long trail persistence
    trail[:] = blur * 0.93


def draw():
    fc = py5.frame_count
    W, H = py5.width, py5.height
    t = fc / TOTAL_FRAMES

    # Update simulation
    update_physarum(t)

    # --- Draw Agent Layer ---
    # Separate species indices for coloring
    ix = pos[:, 0].astype(np.int32)
    iy = pos[:, 1].astype(np.int32)
    s0 = (species == 0)
    s1 = (species == 1)
    s2 = (species == 2)

    agent_layer = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    
    # Species 0: Teal
    c0 = SPECIES_COLORS[0]
    np.add.at(agent_layer[:, :, 0], (iy[s0], ix[s0]), c0[0] * 0.6)
    np.add.at(agent_layer[:, :, 1], (iy[s0], ix[s0]), c0[1] * 0.6)
    np.add.at(agent_layer[:, :, 2], (iy[s0], ix[s0]), c0[2] * 0.6)

    # Species 1: Gold
    c1 = SPECIES_COLORS[1]
    np.add.at(agent_layer[:, :, 0], (iy[s1], ix[s1]), c1[0] * 0.6)
    np.add.at(agent_layer[:, :, 1], (iy[s1], ix[s1]), c1[1] * 0.6)
    np.add.at(agent_layer[:, :, 2], (iy[s1], ix[s1]), c1[2] * 0.6)

    # Species 2: Magenta
    c2 = SPECIES_COLORS[2]
    np.add.at(agent_layer[:, :, 0], (iy[s2], ix[s2]), c2[0] * 0.6)
    np.add.at(agent_layer[:, :, 1], (iy[s2], ix[s2]), c2[1] * 0.6)
    np.add.at(agent_layer[:, :, 2], (iy[s2], ix[s2]), c2[2] * 0.6)

    # Light blur for glow bloom on agents
    agent_blur = (
        agent_layer
        + np.roll(agent_layer, 1, 0) + np.roll(agent_layer, -1, 0)
        + np.roll(agent_layer, 1, 1) + np.roll(agent_layer, -1, 1)
    ) / 5.0

    # Map trail intensity to HSB-derived RGB via LUT
    trail_clamped = np.clip(trail, 0, 255).astype(np.int32)
    trail_rgb = lut_rgb[trail_clamped]

    # Combine trail and agents (additive blend)
    combined = np.clip(trail_rgb + agent_blur * 1.5, 0, 255)

    # Pack to signed int32 ARGB format
    argb = (
        (np.int32(255) << 24)
        | (combined[:, :, 0].astype(np.int32) << 16)
        | (combined[:, :, 1].astype(np.int32) << 8)
        | combined[:, :, 2].astype(np.int32)
    )
    argb_signed = argb.view(np.int32).flatten()

    pimg.load_pixels()
    pimg.pixels[:] = argb_signed
    pimg.update_pixels()

    # --- Draw to 4K Canvas with slow camera motion ---
    py5.background(1, 1, 3)

    # Slow cinematic camera zoom & drift
    zoom = 1.0 + 0.1 * math.sin(t * math.pi)
    rot = 0.04 * math.sin(t * math.pi * 0.5)
    cx_offset = 20 * math.cos(t * math.pi * 2)
    cy_offset = 20 * math.sin(t * math.pi * 2)

    py5.push_matrix()
    py5.translate(W / 2 + cx_offset, H / 2 + cy_offset)
    py5.rotate(rot)
    py5.scale(zoom)
    py5.image(pimg, -W / 2, -H / 2, W, H)
    py5.pop_matrix()

    # --- HUD overlay ---
    scale_x = W / SIM_W
    ts = int(10 * scale_x)
    py5.no_stroke()

    # Dark panel
    panel_w = int(280 * scale_x)
    panel_h = int(95 * scale_x)
    py5.fill(0, 0, 10, 200)
    py5.rect(0, 0, panel_w, panel_h, 0, 0, 8, 0)

    # Title
    py5.fill(160, 220, 240)
    py5.text_size(ts)
    py5.text("PHYSARUM SLIME MOLD NET", int(10 * scale_x), int(18 * scale_x))

    # Stats
    py5.text_size(int(8 * scale_x))
    py5.fill(185, 120, 220)
    py5.text(f"Agents:       {N:,}", int(10 * scale_x), int(38 * scale_x))
    py5.text(f"Decay rate:   0.93", int(10 * scale_x), int(52 * scale_x))
    
    # Calculate active network percentage
    active_pct = (trail > 10.0).mean() * 100.0
    py5.text(f"Coverage:     {active_pct:.2f}%", int(10 * scale_x), int(66 * scale_x))

    # Species breakdown indicators
    dot_y = int(80 * scale_x)
    dot_r = int(4 * scale_x)
    py5.fill(185, 200, 240) # cyan
    py5.circle(int(15 * scale_x), dot_y, dot_r)
    py5.fill(45, 220, 240)  # gold
    py5.circle(int(65 * scale_x), dot_y, dot_r)
    py5.fill(320, 200, 240) # magenta
    py5.circle(int(115 * scale_x), dot_y, dot_r)
    py5.fill(0, 0, 220)
    py5.text("Multi-Species Network", int(135 * scale_x), dot_y + int(3 * scale_x))

    # Progress bar
    py5.fill(0, 0, 20)
    py5.rect(0, H - int(5 * scale_x), W, int(5 * scale_x))
    py5.fill(160, 200, 220)
    py5.rect(0, H - int(5 * scale_x), int(W * t), int(5 * scale_x))

    # Watermark
    py5.fill(185, 60, 140, 100)
    py5.text_size(int(7 * scale_x))
    py5.text(WORK_NAME, int(10 * scale_x), H - int(10 * scale_x))

    # Fail-safe
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {fc}. Aborting.")
            import os
            os._exit(1)

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | Coverage: {active_pct:.2f}%")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames removed.")

        import os
        os._exit(0)


py5.run_sketch()
