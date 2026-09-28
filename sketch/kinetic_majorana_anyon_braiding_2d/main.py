"""
kinetic_majorana_anyon_braiding_2d
----------------------------------
Kinetic 2D simulation of non-Abelian anyon braiding, topological Berry phase singularities,
and chiral Majorana edge currents in a fractional quantum Hall / p+ip topological superconductor thin film.

Features:
- 6 Majorana zero modes (MZMs) bound to quantized vortex cores performing topological
  braiding operations (sigma_i braid group generators) along closed Lissajous paths.
- Collective Laughlin-Moore-Read topological wavefunctions with complex polynomial zeros
  generating intricate Moiré quantum interference fringes and Berry phase streamlines.
- Underlying triangular pinning lattice potential interacting with the order parameter field.
- Dual-light Blinn-Phong specular topological chrome normal shading on the superconducting substrate.
- Dynamic quantum tunneling filaments arcing between entangled pairs.
- Fading worldline ribbons tracing the anyon spacetime braids with chromatic glow.
- Chiral boundary edge currents circulating along the quantum Hall droplet perimeter.
- Adiabatic fusion channel sparks emitted at anyon exchange periapsis.
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_majorana_anyon_braiding_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

# Rendering parameters
SIZE = (1920, 1080)
TOTAL_FRAMES = 900
FPS = 60

# Physics & Grid parameters
GRID_W, GRID_H = 384, 216
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)
GZ = (GX + 1j * GY).astype(np.complex64)
R_SQ = GX * GX + GY * GY
GAUSSIAN_ENVELOPE = np.exp(-R_SQ / 32.0).astype(np.float32)

# Underlying triangular pinning lattice potential
K_LAT = 1.8
V_LAT = (
    np.cos(K_LAT * GX) +
    np.cos(K_LAT * (0.5 * GX + 0.866 * GY)) +
    np.cos(K_LAT * (0.5 * GX - 0.866 * GY))
) / 3.0

# Normal mapping lighting vectors
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.577, 0.577, 0.577], dtype=np.float32)

# Anyon configuration: 6 Majorana Zero Modes in 3 coupled braid pairs
ANYON_COLORS = [
    (0, 240, 255),    # Electric Cyan
    (50, 255, 180),   # Glacial Mint
    (255, 0, 140),    # Neon Fuchsia
    (180, 50, 255),   # Ultraviolet Violet
    (255, 190, 40),   # Radiant Amber Gold
    (255, 255, 255),  # Diamond White
]

# History trails for worldlines
TRAIL_LEN = 110
trail_history = [[] for _ in range(6)]

# Chiral edge state particles
NUM_EDGE_PARTICLES = 1200

# Stream tracer particles (160 streamlines)
np.random.seed(42)
STREAM_SEEDS_X = np.random.uniform(-8.2, 8.2, 160).astype(np.float32)
STREAM_SEEDS_Y = np.random.uniform(-4.6, 4.6, 160).astype(np.float32)

# Fusion sparks
class FusionSpark:
    def __init__(self, x, y, vx, vy, color, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life

sparks = []


def get_anyon_positions(t_norm):
    """
    Computes exact periodic positions of 6 Majorana anyons at normalized time t_norm in [0, 1).
    Braids complete exactly one closed topological cycle at t_norm = 1.0.
    """
    tau = 2.0 * np.pi * t_norm
    pos = np.zeros((6, 2), dtype=np.float32)

    # Pair 0 (MZMs 0 & 1): Central lemniscate / figure-8 braid
    scale0 = 3.6
    pos[0, 0] = scale0 * np.sin(tau)
    pos[0, 1] = scale0 * 0.48 * np.sin(2.0 * tau)
    pos[1, 0] = scale0 * np.sin(tau + np.pi)
    pos[1, 1] = scale0 * 0.48 * np.sin(2.0 * (tau + np.pi))

    # Pair 1 (MZMs 2 & 3): Trefoil-modulated outer orbit (right flank)
    center1_x = 5.2 * np.cos(tau * 0.5)
    center1_y = 2.4 * np.sin(tau * 0.5)
    r1 = 1.6 + 0.35 * np.cos(3.0 * tau)
    pos[2, 0] = center1_x + r1 * np.cos(2.0 * tau)
    pos[2, 1] = center1_y + r1 * np.sin(2.0 * tau)
    pos[3, 0] = center1_x + r1 * np.cos(2.0 * tau + np.pi)
    pos[3, 1] = center1_y + r1 * np.sin(2.0 * tau + np.pi)

    # Pair 2 (MZMs 4 & 5): Counter-rotating orbit (left flank)
    center2_x = -5.2 * np.cos(tau * 0.5)
    center2_y = -2.4 * np.sin(tau * 0.5)
    r2 = 1.6 + 0.35 * np.cos(3.0 * tau)
    pos[4, 0] = center2_x + r2 * np.cos(-2.0 * tau)
    pos[4, 1] = center2_y + r2 * np.sin(-2.0 * tau)
    pos[5, 0] = center2_x + r2 * np.cos(-2.0 * tau + np.pi)
    pos[5, 1] = center2_y + r2 * np.sin(-2.0 * tau + np.pi)

    return pos


def compute_quantum_hall_field(anyon_pos, t_norm):
    """
    Computes collective Laughlin-Moore-Read wavefunction, Moiré interference fringes,
    and Blinn-Phong specular normals on 384x216 grid.
    """
    tau = 2.0 * np.pi * t_norm
    psi = np.ones_like(GZ, dtype=np.complex64)

    for i in range(6):
        zk = anyon_pos[i, 0] + 1j * anyon_pos[i, 1]
        psi *= (GZ - zk) * 0.4

    psi *= GAUSSIAN_ENVELOPE
    u = np.real(psi)
    v = np.imag(psi)
    prob_density = u * u + v * v
    phase = np.angle(psi)

    # Quantum interference fringes & equipotential ripples
    fringe1 = np.cos(4.0 * phase - 2.0 * tau)
    fringe2 = np.cos(2.0 * u + 2.0 * v)
    fringe = 0.5 * (fringe1 + fringe2)

    # Mesa boundary mask
    r_drop = np.sqrt((GX / 8.8)**2 + (GY / 5.0)**2)
    droplet_mask = 1.0 - np.clip(np.tanh((r_drop - 1.0) * 10.0) * 0.5 + 0.5, 0.0, 1.0)

    # Combined height field for Blinn-Phong specular chrome normals
    h_field = (0.35 + 0.35 * fringe + 0.15 * V_LAT + 0.15 * np.tanh(prob_density * 4.0)) * droplet_mask

    # Normal mapping
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * (0.5 * GRID_W / 19.2)
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * (0.5 * GRID_H / 10.8)

    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nz = inv_len
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len

    # Dual Blinn-Phong highlights
    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(dot1, 28.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(dot2, 18.0)

    # Shading computation
    norm_fringe = (fringe + 1.0) * 0.5

    red = 6.0 + 40.0 * np.power(norm_fringe, 2.5) + spec1 * 220.0 * 0.2 + spec2 * 255.0 * 0.85
    green = 10.0 + 130.0 * np.power(norm_fringe, 1.5) + spec1 * 255.0 * 0.95 + spec2 * 170.0 * 0.4
    blue = 24.0 + 190.0 * norm_fringe + spec1 * 255.0 * 1.0 + spec2 * 60.0 * 0.1

    mesa_fade = droplet_mask * 0.96 + 0.04
    red = np.clip(red * mesa_fade, 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * mesa_fade, 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * mesa_fade, 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1)


def settings():
    py5.size(SIZE[0], SIZE[1], py5.P2D)


def setup():
    py5.frame_rate(FPS)
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[Setup Complete] Rendering {WORK_NAME} ({SIZE[0]}x{SIZE[1]} @ {FPS}fps, {TOTAL_FRAMES} frames)...")


def draw():
    frame = py5.frame_count
    t_norm = (frame % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    # 1. Anyon positions
    anyon_pos = get_anyon_positions(t_norm)

    # 2. Compute background wavefield & specular normals
    bg_rgb = compute_quantum_hall_field(anyon_pos, t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    def to_screen(x, y):
        sx = (x + 9.6) / 19.2 * SIZE[0]
        sy = (5.4 - y) / 10.8 * SIZE[1]
        return sx, sy

    # 3. Quantum Hall droplet edge rings
    cx, cy = SIZE[0] / 2.0, SIZE[1] / 2.0
    rx, ry = 8.8 / 9.6 * (SIZE[0] / 2.0), 5.0 / 5.4 * (SIZE[1] / 2.0)
    py5.push_matrix()
    py5.no_fill()
    py5.stroke(0, 240, 255, 70)
    py5.stroke_weight(2.5)
    py5.ellipse(cx, cy, rx * 2.0, ry * 2.0)
    py5.stroke(180, 50, 255, 40)
    py5.stroke_weight(1.2)
    py5.ellipse(cx, cy, rx * 2.0 * 0.98, ry * 2.0 * 0.98)
    py5.pop_matrix()

    # 4. Chiral edge streaming dots
    for i in range(NUM_EDGE_PARTICLES):
        th = (i / float(NUM_EDGE_PARTICLES)) * 2.0 * np.pi + tau * 0.8
        rf = 1.0 + 0.025 * np.sin(8.0 * th + 2.0 * tau)
        px = cx + rx * rf * np.cos(th)
        py_pt = cy + ry * rf * np.sin(th)
        c_val = (np.sin(th * 4.0 + tau) + 1.0) * 0.5
        py5.stroke(int(255 * c_val), int(200 * (1 - c_val) + 100 * c_val), int(255 * (1 - c_val)), 180)
        py5.stroke_weight(1.8)
        py5.point(px, py_pt)

    # 5. Superfluid vortex stream traces (field streamlines)
    for s_idx in range(len(STREAM_SEEDS_X)):
        # Animate seeds slowly along closed orbits
        s_th = s_idx * 0.039 + tau
        px = STREAM_SEEDS_X[s_idx] + 0.15 * np.cos(s_th)
        py_s = STREAM_SEEDS_Y[s_idx] + 0.15 * np.sin(s_th)
        trail = []
        for step in range(16):
            trail.append(to_screen(px, py_s))
            # Biot-Savart vortex velocity field
            vx, vy = 0.0, 0.0
            for k in range(6):
                dx = px - anyon_pos[k, 0]
                dy = py_s - anyon_pos[k, 1]
                r2 = dx * dx + dy * dy + 0.25
                vx += -dy / r2 * 0.10
                vy += dx / r2 * 0.10
            px += vx
            py_s += vy

        for seg in range(len(trail) - 1):
            al = int(110 * (seg / float(len(trail))))
            py5.stroke(0, 220, 255, al)
            py5.stroke_weight(1.2)
            py5.line(trail[seg][0], trail[seg][1], trail[seg + 1][0], trail[seg + 1][1])

    # 6. Braided worldline ribbons
    for i in range(6):
        sx, sy = to_screen(anyon_pos[i, 0], anyon_pos[i, 1])
        trail_history[i].append((sx, sy))
        if len(trail_history[i]) > TRAIL_LEN:
            trail_history[i].pop(0)

        t_len = len(trail_history[i])
        if t_len > 2:
            base_col = ANYON_COLORS[i]
            for seg in range(t_len - 1):
                al = int(255.0 * (seg / float(t_len))**1.7 * 0.9)
                w = 1.2 + 5.0 * (seg / float(t_len))
                p0 = trail_history[i][seg]
                p1 = trail_history[i][seg + 1]
                py5.stroke(base_col[0], base_col[1], base_col[2], al)
                py5.stroke_weight(w)
                py5.line(p0[0], p0[1], p1[0], p1[1])

    # 7. Quantum tunneling filaments between anyon pairs
    for p_idx, (idxA, idxB) in enumerate([(0, 1), (2, 3), (4, 5)]):
        dist = np.linalg.norm(anyon_pos[idxA] - anyon_pos[idxB])
        if dist < 4.2:
            sA = to_screen(anyon_pos[idxA, 0], anyon_pos[idxA, 1])
            sB = to_screen(anyon_pos[idxB, 0], anyon_pos[idxB, 1])
            tunnel_alpha = int(220.0 * (1.0 - dist / 4.2))
            py5.stroke(255, 255, 255, tunnel_alpha)
            py5.stroke_weight(2.0)
            segments = 14
            last_pt = sA
            for s in range(1, segments):
                frac = s / float(segments)
                mid_x = sA[0] * (1 - frac) + sB[0] * frac + np.sin(tau * 12.0 + s * 3.0 + p_idx) * 14.0
                mid_y = sA[1] * (1 - frac) + sB[1] * frac + np.cos(tau * 12.0 + s * 3.0 + p_idx) * 14.0
                py5.line(last_pt[0], last_pt[1], mid_x, mid_y)
                last_pt = (mid_x, mid_y)
            py5.line(last_pt[0], last_pt[1], sB[0], sB[1])

    # 8. Adiabatic fusion channel sparks
    dist_pair0 = np.linalg.norm(anyon_pos[0] - anyon_pos[1])
    if dist_pair0 < 1.0 and frame % 4 == 0:
        mid_x = (anyon_pos[0, 0] + anyon_pos[1, 0]) * 0.5
        mid_y = (anyon_pos[0, 1] + anyon_pos[1, 1]) * 0.5
        smx, smy = to_screen(mid_x, mid_y)
        for _ in range(8):
            angle = np.random.uniform(0, 2 * np.pi)
            spd = np.random.uniform(3.0, 9.0)
            sparks.append(FusionSpark(
                smx, smy,
                spd * np.cos(angle), spd * np.sin(angle),
                (255, 255, 255),
                np.random.randint(20, 45)
            ))

    active_sparks = []
    for sp in sparks:
        sp.x += sp.vx
        sp.y += sp.vy
        sp.vx *= 0.94
        sp.vy *= 0.94
        sp.life -= 1
        if sp.life > 0:
            al = int(255.0 * (sp.life / float(sp.max_life)))
            py5.stroke(sp.color[0], sp.color[1], sp.color[2], al)
            py5.stroke_weight(2.0)
            py5.line(sp.x, sp.y, sp.x - sp.vx * 2.0, sp.y - sp.vy * 2.0)
            active_sparks.append(sp)
    sparks[:] = active_sparks

    # 9. Render Majorana Anyon Cores & Berry Phase Halos
    for i in range(6):
        sx, sy = to_screen(anyon_pos[i, 0], anyon_pos[i, 1])
        base_col = ANYON_COLORS[i]

        py5.no_fill()
        for ring_idx in range(5):
            ring_r = 14.0 + ring_idx * 15.0 + 3.0 * np.sin(tau * 4.0 + i + ring_idx)
            ring_alpha = int(160.0 / (ring_idx + 1.0))
            py5.stroke(base_col[0], base_col[1], base_col[2], ring_alpha)
            py5.stroke_weight(1.5)
            py5.ellipse(sx, sy, ring_r * 2.0, ring_r * 2.0)

        # Luminous Anyon Core
        py5.no_stroke()
        py5.fill(base_col[0], base_col[1], base_col[2], 90)
        py5.ellipse(sx, sy, 36, 36)
        py5.fill(base_col[0], base_col[1], base_col[2], 190)
        py5.ellipse(sx, sy, 20, 20)
        py5.fill(255, 255, 255, 255)
        py5.ellipse(sx, sy, 8, 8)

    # 10. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] Majorana anyon braiding preview captured: {PREVIEW_PNG}")

    if frame % 60 == 0:
        pct = (frame / float(TOTAL_FRAMES)) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%) | Sparks: {len(sparks)}")

    # 11. Completion and Video Encoding
    if frame >= TOTAL_FRAMES:
        print("[Rendering Complete] Encoding master MP4 via ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(FRAMES_DIR, "frame-%04d.png"),
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "5.1",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "fast",
            OUTPUT_MP4
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ffmpeg ERROR] {result.stderr}")
        else:
            print(f"[Video Compiled] Master MP4 saved: {OUTPUT_MP4}")

        # Cleanup frame images
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
