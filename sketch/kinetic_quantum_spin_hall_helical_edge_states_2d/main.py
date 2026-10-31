"""
kinetic_quantum_spin_hall_helical_edge_states_2d
2D quantum condensed matter physics simulation of the Quantum Spin Hall (QSH) effect
in a Bernevig-Hughes-Zhang (BHZ) / Kane-Mele Z2 topological insulator.
Demonstrates bulk bandgap insulation, Kramers-paired helical edge channels with strict
spin-momentum locking (spin-up clockwise, spin-down counter-clockwise), and topological
dissipationless transport immune to non-magnetic impurity scattering.

Format: 720 frames @ 60 FPS (12.0s seamless loop)
Native Output: 3840x2160 (Retina 4K master)
"""

import os
import shutil
import subprocess
import sys
import numpy as np
import py5

# Work configuration
WORK_NAME = "kinetic_quantum_spin_hall_helical_edge_states_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180  # 25% progress

# Low-res computational tensor grid for 4K background synthesis
GW, GH = 480, 270

# Particle configuration
NUM_PARTICLES = 2400
TRAIL_LEN = 8


def sdf_rounded_box(x, y, bx, by, r):
    """Signed distance function to a rounded rectangle with half-extents (bx, by) and radius r."""
    qx = np.abs(x) - (bx - r)
    qy = np.abs(y) - (by - r)
    ax = np.maximum(qx, 0.0)
    ay = np.maximum(qy, 0.0)
    outer = np.sqrt(ax ** 2 + ay ** 2)
    inner = np.minimum(np.maximum(qx, qy), 0.0)
    return outer + inner - r


class QSHSimulation:
    def __init__(self, gw=GW, gh=GH):
        self.gw = gw
        self.gh = gh

        # Coordinate grid: aspect ratio 16:9, centered at origin
        x = np.linspace(-3.555, 3.555, gw, dtype=np.float32)
        y = np.linspace(-2.0, 2.0, gh, dtype=np.float32)
        self.X, self.Y = np.meshgrid(x, y)

        # Topological quantum well boundary parameters
        self.bx = 2.75
        self.by = 1.35
        self.rc = 0.40

        # Calculate base SDF to the rounded quantum well boundary
        self.d_base = sdf_rounded_box(self.X, self.Y, self.bx, self.by, self.rc)

        # Non-magnetic boundary impurities (potential obstacles that helical states glide around)
        self.defects = [
            (0.0, 1.35, 0.18),    # Top edge center
            (1.8, -1.35, 0.16),   # Bottom edge right
            (-2.75, 0.0, 0.18),   # Left edge center
            (2.75, 0.3, 0.16),    # Right edge upper
        ]

        # Modify SDF to smoothly curve around defects
        self.d_field = self.d_base.copy()
        for dx_c, dy_c, dr in self.defects:
            dist_defect = np.sqrt((self.X - dx_c) ** 2 + (self.Y - dy_c) ** 2)
            # Push boundary outward smoothly around defects
            defect_bulge = np.maximum(0.0, dr - dist_defect) * 1.2
            self.d_field += defect_bulge

        # Normal vector and tangent vector along the perimeter
        # Normal n = grad(d) / |grad(d)|
        ddx = np.gradient(self.d_field, axis=1) * (self.gw / 7.11)
        ddy = np.gradient(self.d_field, axis=0) * (self.gh / 4.0)
        grad_norm = np.sqrt(ddx ** 2 + ddy ** 2) + 1e-6
        self.nx = ddx / grad_norm
        self.ny = ddy / grad_norm

        # Tangent vector: t = (-ny, nx) points counter-clockwise
        self.tx = -self.ny
        self.ty = self.nx

        # Edge state envelope: localized at boundary d = 0 with decay length xi = 0.18
        self.edge_envelope = np.exp(-np.abs(self.d_field) / 0.18)

        # Inverted bandgap bulk envelope: inside the ribbon (d < -0.1)
        self.bulk_mask = np.clip((-self.d_field - 0.05) / 0.25, 0.0, 1.0)

        # Precompute perimeter coordinate s(x, y) via polar-like angle along rounded box
        self.perimeter_s = np.arctan2(self.Y, self.X)

        # Initialize Lagrangian spin-polarized quasiparticles
        self.num_particles = NUM_PARTICLES
        self.trail_len = TRAIL_LEN

        # Particles placed primarily along the perimeter edge (d ~ 0)
        rng = np.random.default_rng(20261030)
        # Half spin-up, half spin-down
        self.p_spin = np.array([1] * (self.num_particles // 2) + [-1] * (self.num_particles // 2), dtype=np.int32)

        # Angles around perimeter
        angles = rng.uniform(-np.pi, np.pi, self.num_particles).astype(np.float32)
        # Approximate perimeter points
        rad_x = (self.bx - 0.05)
        rad_y = (self.by - 0.05)
        self.p_x = rad_x * np.cos(angles) + rng.normal(0, 0.04, self.num_particles).astype(np.float32)
        self.p_y = rad_y * np.sin(angles) + rng.normal(0, 0.04, self.num_particles).astype(np.float32)

        # Velocities
        self.p_vx = np.zeros(self.num_particles, dtype=np.float32)
        self.p_vy = np.zeros(self.num_particles, dtype=np.float32)

        # Trail buffers
        self.trail_x = np.repeat(self.p_x[:, None], self.trail_len, axis=1)
        self.trail_y = np.repeat(self.p_y[:, None], self.trail_len, axis=1)

    def compute_fields(self, t):
        """
        Compute 2D quantum spin Hall fields:
        1. Bulk inverted bandgap topology with Berry curvature texture.
        2. Spin-Up clockwise helical current (electric cyan).
        3. Spin-Down counter-clockwise helical current (laser magenta).
        4. Defect scattering immunity nodes (blinding solar gold).
        5. Dual-light Blinn-Phong specular relief normal mapping.
        """
        tau = 2.0 * np.pi * t

        # Wave propagation phases along the perimeter
        # Spin-Up: clockwise (-tau)
        phase_up = 10.0 * self.perimeter_s - 2.0 * tau
        # Spin-Down: counter-clockwise (+tau)
        phase_down = -10.0 * self.perimeter_s - 2.0 * tau

        # Helical edge current intensities
        wave_up = (0.5 + 0.5 * np.cos(phase_up)) * self.edge_envelope
        wave_down = (0.5 + 0.5 * np.cos(phase_down)) * self.edge_envelope

        # Bulk inverted Dirac bandgap wavefunction (dim Mexican-hat standing oscillation)
        bulk_k = np.sqrt(self.X ** 2 + self.Y ** 2)
        bulk_mode = (np.cos(6.0 * bulk_k - tau) * np.sin(3.0 * self.X + 3.0 * self.Y)) * self.bulk_mask

        # Surface normal relief mapping: compute gradients of total quantum density
        density = 1.4 * (wave_up + wave_down) + 0.25 * bulk_mode
        ddx = np.gradient(density, axis=1) * (self.gw / 7.11)
        ddy = np.gradient(density, axis=0) * (self.gh / 4.0)

        norm = np.sqrt(ddx ** 2 + ddy ** 2 + 1.0)
        nx = -ddx / norm
        ny = -ddy / norm
        nz = 1.0 / norm

        # Key specular light (cyan-tinted, top-left)
        lx1, ly1, lz1 = -0.577, 0.577, 0.577
        dot1 = np.maximum(0.0, nx * lx1 + ny * ly1 + nz * lz1)
        spec1 = dot1 ** 8

        # Fill specular light (magenta-tinted, bottom-right)
        lx2, ly2, lz2 = 0.577, -0.577, 0.577
        dot2 = np.maximum(0.0, nx * lx2 + ny * ly2 + nz * lz2)
        spec2 = dot2 ** 6

        # Synthesize RGB buffer
        # Base: Deep Obsidian Cryogenic Void
        r = np.full((self.gh, self.gw), 3.0, dtype=np.float32)
        g = np.full((self.gh, self.gw), 5.0, dtype=np.float32)
        b = np.full((self.gh, self.gw), 11.0, dtype=np.float32)

        # Inverted bandgap bulk interior (Midnight Indigo & Amethyst)
        r += self.bulk_mask * 15.0 + np.maximum(0.0, bulk_mode) * 20.0
        g += self.bulk_mask * 18.0 + np.maximum(0.0, bulk_mode) * 30.0
        b += self.bulk_mask * 42.0 + np.maximum(0.0, bulk_mode) * 65.0

        # Spin-Up Helical Current (Electric Glacial Cyan & Emerald Mint)
        r += wave_up * 10.0
        g += wave_up * 215.0
        b += wave_up * 245.0

        # Spin-Down Helical Current (Radiant Laser Cerise & Neon Magenta)
        r += wave_down * 245.0
        g += wave_down * 25.0
        b += wave_down * 135.0

        # Helical crossing nodes: where spin-up and spin-down overlap along the edge
        overlap = (wave_up * wave_down) ** 0.8
        r += overlap * 160.0
        g += overlap * 210.0
        b += overlap * 255.0

        # Defect immunity nodes (Blinding Solar Amber & White Gold)
        for dx_c, dy_c, dr in self.defects:
            dist_d = np.sqrt((self.X - dx_c) ** 2 + (self.Y - dy_c) ** 2)
            node_glow = np.exp(-dist_d / (dr * 0.8)) * 1.5
            r += node_glow * 255.0
            g += node_glow * 200.0
            b += node_glow * 40.0

        # Specular sheen relief
        r += spec1 * 110.0 + spec2 * 140.0
        g += spec1 * 180.0 + spec2 * 70.0
        b += spec1 * 210.0 + spec2 * 160.0

        rgb = np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
        return rgb

    def update_particles(self, t):
        """
        Advect Lagrangian spin-polarized quasiparticles.
        Strict spin-momentum locking:
        - Spin +1 (Spin-Up): Driven clockwise (-t_vec) along the boundary.
        - Spin -1 (Spin-Down): Driven counter-clockwise (+t_vec) along the boundary.
        - Bound tightly to the edge d = 0 via normal restoring potential.
        - Glide seamlessly around non-magnetic defects without backscattering.
        """
        tau = 2.0 * np.pi * t

        # Roll trail buffers
        self.trail_x = np.roll(self.trail_x, 1, axis=1)
        self.trail_y = np.roll(self.trail_y, 1, axis=1)
        self.trail_x[:, 0] = self.p_x
        self.trail_y[:, 0] = self.p_y

        # Compute signed distance and normal/tangent vectors at particle positions
        # Using analytical rounded box gradient
        d_p = sdf_rounded_box(self.p_x, self.p_y, self.bx, self.by, self.rc)

        # Analytical normal vector for rounded rectangle
        qx = np.abs(self.p_x) - (self.bx - self.rc)
        qy = np.abs(self.p_y) - (self.by - self.rc)
        ax = np.maximum(qx, 0.0)
        ay = np.maximum(qy, 0.0)
        a_norm = np.sqrt(ax ** 2 + ay ** 2) + 1e-6
        # Outer unit normal
        nx_p = np.sign(self.p_x) * (ax / a_norm)
        ny_p = np.sign(self.p_y) * (ay / a_norm)

        # For inner points, dominant axis
        inner_mask = (qx < 0) & (qy < 0)
        dom_x = qx > qy
        nx_p[inner_mask & dom_x] = np.sign(self.p_x[inner_mask & dom_x])
        ny_p[inner_mask & dom_x] = 0.0
        nx_p[inner_mask & (~dom_x)] = 0.0
        ny_p[inner_mask & (~dom_x)] = np.sign(self.p_y[inner_mask & (~dom_x)])

        # Defect avoidance: push particles smoothly around impurities
        for dx_c, dy_c, dr in self.defects:
            dx = self.p_x - dx_c
            dy = self.p_y - dy_c
            dist_sq = dx ** 2 + dy ** 2 + 1e-6
            dist = np.sqrt(dist_sq)
            in_defect = dist < (dr * 1.5)
            if np.any(in_defect):
                push_mag = (dr * 1.5 - dist[in_defect]) * 3.5
                nx_p[in_defect] += push_mag * (dx[in_defect] / dist[in_defect])
                ny_p[in_defect] += push_mag * (dy[in_defect] / dist[in_defect])

        # Renormalize normal vector
        norm_p = np.sqrt(nx_p ** 2 + ny_p ** 2) + 1e-6
        nx_p /= norm_p
        ny_p /= norm_p

        # Tangent vector: t = (-ny, nx) is counter-clockwise
        tx_p = -ny_p
        ty_p = nx_p

        # Spin-momentum locked driving velocity:
        # Spin +1: clockwise (-t)
        # Spin -1: counter-clockwise (+t)
        v_fermi = 1.65
        vx_target = -self.p_spin * tx_p * v_fermi
        vy_target = -self.p_spin * ty_p * v_fermi

        # Strong restoring force pulling particles to the edge d = 0
        restore_k = 6.5
        fx_restore = -restore_k * d_p * nx_p
        fy_restore = -restore_k * d_p * ny_p

        # Combine with inertia and damping
        dt = 0.016
        self.p_vx = self.p_vx * 0.82 + (vx_target + fx_restore) * 0.18
        self.p_vy = self.p_vy * 0.82 + (vy_target + fy_restore) * 0.18

        # Position integration
        new_x = self.p_x + self.p_vx * dt
        new_y = self.p_y + self.p_vy * dt

        # Recycle stray particles that escape the edge channel
        escape_mask = np.abs(d_p) > 0.65
        if np.any(escape_mask):
            num_esc = np.sum(escape_mask)
            rng = np.random.default_rng()
            rand_angles = rng.uniform(-np.pi, np.pi, num_esc).astype(np.float32)
            new_x[escape_mask] = (self.bx - 0.05) * np.cos(rand_angles)
            new_y[escape_mask] = (self.by - 0.05) * np.sin(rand_angles)
            self.p_vx[escape_mask] = 0.0
            self.p_vy[escape_mask] = 0.0
            # Reset history buffer to prevent screen-spanning streak lines
            self.trail_x[escape_mask, :] = new_x[escape_mask, None]
            self.trail_y[escape_mask, :] = new_y[escape_mask, None]

        self.p_x = new_x
        self.p_y = new_y


# Global simulation instance
sim = None


def setup():
    global sim
    py5.size(1920, 1080, py5.P2D)
    py5.frame_rate(FPS)
    sim = QSHSimulation(GW, GH)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    global sim
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        return

    t = (frame - 1) / float(TOTAL_FRAMES)

    # 1. Compute vectorized 2D Quantum Spin Hall & specular field
    rgb_field = sim.compute_fields(t)

    # Draw background field
    bg_img = py5.create_image_from_numpy(rgb_field, 'RGB')
    py5.image(bg_img, 0, 0, py5.width, py5.height)

    # 2. Update Lagrangian spin-polarized quasiparticles
    sim.update_particles(t)

    # 3. Vectorized rendering of helical trajectory ribbons
    # Convert simulation coordinates (-3.555..3.555, -2.0..2.0) to screen pixel coordinates
    sx = (sim.trail_x + 3.555) / 7.11 * py5.width
    sy = (sim.trail_y + 2.0) / 4.0 * py5.height

    # Filter out wrap-around / jump lines
    dist_threshold_sq = (0.25 * py5.width) ** 2
    py5.stroke_weight(1.6)

    # Batch draw trail segments
    for seg in range(sim.trail_len - 1):
        x0 = sx[:, seg]
        y0 = sy[:, seg]
        x1 = sx[:, seg + 1]
        y1 = sy[:, seg + 1]

        valid = ((x1 - x0) ** 2 + (y1 - y0) ** 2) < dist_threshold_sq

        # Spin-Up (Clockwise Helical Streamlines: Electric Glacial Cyan & Emerald)
        mask_up = valid & (sim.p_spin == 1)
        if np.any(mask_up):
            alpha_up = int(230 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(0, 240, 255, alpha_up)
            lines_up = np.column_stack([x0[mask_up], y0[mask_up], x1[mask_up], y1[mask_up]])
            py5.lines(lines_up)

        # Spin-Down (Counter-Clockwise Helical Streamlines: Neon Laser Cerise & Magenta)
        mask_down = valid & (sim.p_spin == -1)
        if np.any(mask_down):
            alpha_down = int(230 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(244, 63, 94, alpha_down)
            lines_down = np.column_stack([x0[mask_down], y0[mask_down], x1[mask_down], y1[mask_down]])
            py5.lines(lines_down)

    # Batch draw particle spark heads
    head_x = sx[:, 0]
    head_y = sy[:, 0]

    # Spin-Up Sparks (Diamond Glacial White / Cyan)
    mask_pts_up = (sim.p_spin == 1)
    py5.stroke_weight(3.0)
    py5.stroke(210, 255, 255, 250)
    pts_up = np.column_stack([head_x[mask_pts_up], head_y[mask_pts_up]])
    py5.points(pts_up)

    # Spin-Down Sparks (Neon Laser Rose / Pearl Magenta)
    mask_pts_down = (sim.p_spin == -1)
    py5.stroke_weight(3.0)
    py5.stroke(255, 215, 235, 250)
    pts_down = np.column_stack([head_x[mask_pts_down], head_y[mask_pts_down]])
    py5.points(pts_down)

    # 4. Save frame for video compilation
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image at designated frame
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] QSH preview captured: {PREVIEW_PATH}")

    # Progress report
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        progress = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress:.1f}%)")

    # 5. Finalize animation encoding on completion
    if frame == TOTAL_FRAMES:
        print("[Rendering Complete] Encoding master MP4 via ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "17",
            "-preset", "slow",
            OUTPUT_MP4
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[Video Compiled] Master MP4 saved: {OUTPUT_MP4}")
            # Clean up temporary frames directory
            shutil.rmtree(FRAMES_DIR, ignore_errors=True)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
        else:
            print(f"[FFmpeg Error] {res.stderr}")

        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
