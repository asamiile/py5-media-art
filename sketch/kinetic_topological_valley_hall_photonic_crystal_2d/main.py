"""
kinetic_topological_valley_hall_photonic_crystal_2d
---------------------------------------------------
Kinetic 2D topological photonics simulation of backscattering-immune light transport
in a Valley Hall Photonic Crystal (VPC) with broken spatial inversion symmetry.

Features:
- Triangular / honeycomb dielectric resonator lattice with broken spatial inversion symmetry (Delta r = r_A - r_B != 0).
- Topological Valley Chern phase domains (C_V = +/- 1/2 at K and K' valleys).
- Canonical trapezoidal zigzag domain wall interface featuring sharp 60-degree and 120-degree corners.
- Topologically protected evanescent Bloch wavepackets traversing sharp bends with zero backscattering (T ~ 100%).
- Circulating Poynting vector flux micro-vortices at valley extrema.
- Dual-light Blinn-Phong specular dielectric crystal facet shading.
- 120 Poynting energy flux streamline ribbons navigating the sharp corners.
- 2,800 bioluminescent photon wavepacket Dirac quasiparticle sparks.
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_topological_valley_hall_photonic_crystal_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

# Rendering parameters
SIZE = (1920, 1080)
TOTAL_FRAMES = 900
FPS = 60

# Domain & Grid configuration
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Directional lighting vectors for Blinn-Phong specular sheen
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)

# Sharp-corner trapezoidal waveguide path (canonical 60 / 120 degree topological bends)
PATH_X = np.array([-9.6, -4.5, -2.0, 2.0, 4.5, 9.6], dtype=np.float32)
PATH_Y = np.array([-1.4, -1.4,  1.5, 1.5, -1.4, -1.4], dtype=np.float32)


def get_path_metrics(gx, gy):
    """
    Computes orthogonal projection metrics for every grid point to the piecewise
    linear trapezoidal topological waveguide path.
    """
    pts = np.stack([PATH_X, PATH_Y], axis=-1)
    segs = pts[1:] - pts[:-1]
    seg_lens = np.linalg.norm(segs, axis=-1)
    seg_cum = np.concatenate([[0.0], np.cumsum(seg_lens)])
    total_len = seg_cum[-1]

    min_dist_sq = np.full_like(gx, 1e9)
    s_best = np.zeros_like(gx)
    normal_signed = np.zeros_like(gx)
    tangent_x = np.zeros_like(gx)
    tangent_y = np.zeros_like(gx)

    for i in range(len(segs)):
        p0 = pts[i]
        d = segs[i]
        L = seg_lens[i]
        L2 = L * L
        
        t = ((gx - p0[0]) * d[0] + (gy - p0[1]) * d[1]) / L2
        t_clamped = np.clip(t, 0.0, 1.0)
        
        proj_x = p0[0] + t_clamped * d[0]
        proj_y = p0[1] + t_clamped * d[1]
        
        dx = gx - proj_x
        dy = gy - proj_y
        dist_sq = dx * dx + dy * dy
        cross = d[0] * dy - d[1] * dx
        
        mask = dist_sq < min_dist_sq
        min_dist_sq[mask] = dist_sq[mask]
        s_best[mask] = seg_cum[i] + t_clamped[mask] * L
        normal_signed[mask] = np.sign(cross[mask]) * np.sqrt(dist_sq[mask])
        tangent_x[mask] = d[0] / L
        tangent_y[mask] = d[1] / L

    return np.sqrt(min_dist_sq), s_best, normal_signed, tangent_x, tangent_y, total_len


DIST_PATH, S_PATH, N_SIGNED, TAN_X, TAN_Y, TOTAL_LEN = get_path_metrics(GX, GY)


def compute_valley_hall_field(t_norm):
    """
    Computes 2D photonic crystal dielectric resonator potential, inversion-symmetry
    breaking phases, localized edge state intensity, and Blinn-Phong surface normals.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. Triangular Lattice & Dielectric Resonator Pillars
    a_lat = 0.52
    ky = 2.0 * np.pi / (a_lat * np.sqrt(3.0))
    kx = 2.0 * np.pi / a_lat

    k1 = np.cos(kx * x)
    k2 = np.cos(-0.5 * kx * x + ky * y)
    k3 = np.cos(-0.5 * kx * x - ky * y)
    
    # Inversion-symmetry-breaking perturbation (Delta r)
    domain_phase = np.tanh(N_SIGNED / 0.35) # -1 below wall, +1 above wall
    
    lattice_base = (k1 + k2 + k3) / 3.0
    tri_facet = (np.sin(kx * x) + np.sin(-0.5 * kx * x + ky * y) + np.sin(-0.5 * kx * x - ky * y)) / 3.0
    
    dielectric_pillars = lattice_base + 0.48 * domain_phase * tri_facet
    pillars_norm = np.clip((dielectric_pillars + 0.6) / 1.5, 0.0, 1.0)
    pillars_power = np.power(pillars_norm, 3.5)

    # 2. Topologically Protected Propagating Wavepackets
    xi_decay = 0.42 # Tight sub-wavelength confinement
    edge_confinement = np.exp(-(DIST_PATH * DIST_PATH) / (2.0 * xi_decay * xi_decay))
    
    # Propagating wavepackets along arc length
    k_carrier = 8.5
    carrier_phase = k_carrier * S_PATH - tau * 6.0
    wave_carrier = np.cos(carrier_phase)
    
    # Localized solitary envelope packets
    s_packet1 = (tau * 3.2) % TOTAL_LEN
    s_packet2 = (tau * 3.2 + TOTAL_LEN * 0.5) % TOTAL_LEN
    
    d_s1 = np.abs(S_PATH - s_packet1)
    d_s1 = np.minimum(d_s1, TOTAL_LEN - d_s1)
    env1 = np.exp(-(d_s1 * d_s1) / (2.0 * 2.2 * 2.2))
    
    d_s2 = np.abs(S_PATH - s_packet2)
    d_s2 = np.minimum(d_s2, TOTAL_LEN - d_s2)
    env2 = np.exp(-(d_s2 * d_s2) / (2.0 * 2.2 * 2.2))
    
    total_env = np.clip(env1 + env2 + 0.18, 0.0, 1.0)
    edge_mode_intensity = edge_confinement * total_env * (0.4 + 0.6 * np.power(0.5 + 0.5 * wave_carrier, 2.0))

    # 3. Valley Berry Curvature & Optical Vortices
    berry_flux = domain_phase * np.power(pillars_norm, 2.2) * np.exp(-np.abs(N_SIGNED) / 2.5)

    # 4. Specular Normal Mapping
    h_field = (
        0.48 * edge_mode_intensity
        + 0.36 * pillars_power
        + 0.16 * np.abs(berry_flux)
    )
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5
    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len
    nz = inv_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(np.clip((dot1 - 0.50) / 0.50, 0.0, 1.0), 6.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(np.clip((dot2 - 0.50) / 0.50, 0.0, 1.0), 5.0)

    # 5. Color Palette:
    # Top Domain (Valley K): Electric Glacial Cyan (#00f2ff) & Deep Cobalt (#002877)
    # Bottom Domain (Valley K'): Radiant Laser Cerise/Magenta (#ff0077) & Royal Violet (#5500aa)
    # Topological Edge Mode Wavepacket: Incandescent Solar Gold (#ffb700) & Amber Flame (#ff5500)
    # Specular Highlights: Diamond Liquid Chrome (#ffffff)
    # Substrate Void: Midnight Obsidian (#02030d)

    k_dom = np.clip(domain_phase, 0.0, 1.0)
    kp_dom = np.clip(-domain_phase, 0.0, 1.0)

    red = (
        2.0
        + 250.0 * edge_mode_intensity
        + 215.0 * kp_dom * pillars_power
        + 8.0 * k_dom * pillars_power
        + spec1 * 255.0
        + spec2 * 190.0 * 0.8
    )
    green = (
        3.0
        + 170.0 * edge_mode_intensity
        + 12.0 * kp_dom * pillars_power
        + 185.0 * k_dom * pillars_power
        + spec1 * 255.0 * 0.95
        + spec2 * 125.0 * 0.5
    )
    blue = (
        12.0
        + 18.0 * edge_mode_intensity
        + 195.0 * kp_dom * pillars_power
        + 245.0 * k_dom * pillars_power
        + spec1 * 255.0
        + spec2 * 45.0 * 0.2
    )

    vig = np.clip(1.0 - (np.abs(x) / 9.4)**8.0, 0.0, 1.0) * np.clip(1.0 - (np.abs(y) / 5.25)**8.0, 0.0, 1.0)
    red = np.clip(red * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1)


def to_screen(x, y):
    sx = (x + 9.6) / 19.2 * SIZE[0]
    sy = (5.4 - y) / 10.8 * SIZE[1]
    return sx, sy


def settings():
    py5.size(SIZE[0], SIZE[1], py5.P2D)


def setup():
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count
    t_norm = (frame % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    # 1. Background Photonic Crystal & Topological Wavefield
    bg_rgb = compute_valley_hall_field(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Topological Waveguide Pathway (Sharp 60/120 degree bends)
    py5.no_fill()
    py5.stroke(255, 205, 30, 230)
    py5.stroke_weight(2.6)
    py5.begin_shape()
    for i in range(len(PATH_X)):
        sx, sy = to_screen(PATH_X[i], PATH_Y[i])
        py5.vertex(sx, sy)
    py5.end_shape()

    # Outer waveguide boundary rails
    for offset_sign in [-1, 1]:
        if offset_sign > 0:
            py5.stroke(0, 240, 255, 125)
        else:
            py5.stroke(255, 30, 160, 125)
        py5.stroke_weight(1.3)
        py5.begin_shape()
        for i in range(len(PATH_X)):
            sx, sy = to_screen(PATH_X[i], PATH_Y[i] + offset_sign * 0.35)
            py5.vertex(sx, sy)
        py5.end_shape()

    # 3. 120 Poynting Streamline Ribbons Flowing Across Sharp Bends
    pts = np.stack([PATH_X, PATH_Y], axis=-1)
    segs = pts[1:] - pts[:-1]
    seg_lens = np.linalg.norm(segs, axis=-1)
    seg_cum = np.concatenate([[0.0], np.cumsum(seg_lens)])
    total_path_len = seg_cum[-1]

    num_ribbons = 120
    for r in range(num_ribbons):
        seed = r * 0.61803398875
        s_start = ((seed * total_path_len + tau * 3.4) % total_path_len)
        trans_offset = ((r % 7) - 3) * 0.05
        
        ribbon_pts = []
        for step in range(16):
            s_cur = (s_start + step * 0.22) % total_path_len
            seg_idx = np.searchsorted(seg_cum, s_cur) - 1
            seg_idx = np.clip(seg_idx, 0, len(segs) - 1)
            local_t = (s_cur - seg_cum[seg_idx]) / seg_lens[seg_idx]
            
            tx = segs[seg_idx][0] / seg_lens[seg_idx]
            ty = segs[seg_idx][1] / seg_lens[seg_idx]
            nx, ny = -ty, tx
            
            bx = pts[seg_idx][0] + local_t * segs[seg_idx][0] + nx * trans_offset
            by = pts[seg_idx][1] + local_t * segs[seg_idx][1] + ny * trans_offset
            ribbon_pts.append(to_screen(bx, by))

        for s in range(len(ribbon_pts) - 1):
            prg = s / float(len(ribbon_pts))
            al = int(220 * prg)
            if r % 2 == 0:
                py5.stroke(255, 200, 30, al)
            else:
                py5.stroke(0, 245, 255, al)
            py5.stroke_weight(0.9 + 1.2 * prg)
            py5.line(ribbon_pts[s][0], ribbon_pts[s][1], ribbon_pts[s+1][0], ribbon_pts[s+1][1])

    # 4. 2,800 Topologically Guided Photon Wavepackets / Dirac Quasiparticles
    py5.stroke_weight(1.8)
    for p in range(2800):
        seed = p * 0.61803398875
        s_pos = ((seed * total_path_len + tau * 2.8) % total_path_len)
        
        seg_idx = np.searchsorted(seg_cum, s_pos) - 1
        seg_idx = np.clip(seg_idx, 0, len(segs) - 1)
        local_t = (s_pos - seg_cum[seg_idx]) / seg_lens[seg_idx]
        
        tx = segs[seg_idx][0] / seg_lens[seg_idx]
        ty = segs[seg_idx][1] / seg_lens[seg_idx]
        nx, ny = -ty, tx
        
        base_x = pts[seg_idx][0] + local_t * segs[seg_idx][0]
        base_y = pts[seg_idx][1] + local_t * segs[seg_idx][1]
        
        w_offset = (np.sin(p * 3.14 + tau * 6.0) * 0.22) * np.exp(-((p % 30) / 12.0)**2)
        px = base_x + nx * w_offset
        py_cur = base_y + ny * w_offset

        sx, sy = to_screen(px, py_cur)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if p % 6 == 0:
                py5.stroke(255, 255, 255, 250)
                py5.stroke_weight(2.4)
            elif p % 2 == 0:
                py5.stroke(255, 210, 50, 195)
                py5.stroke_weight(1.6)
            else:
                py5.stroke(0, 240, 255, 180)
                py5.stroke_weight(1.3)
            py5.point(sx, sy)

    # 5. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] Topological valley hall preview captured: {PREVIEW_PNG}")

    if frame % 60 == 0:
        pct = (frame / float(TOTAL_FRAMES)) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 6. Completion and Video Encoding
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
