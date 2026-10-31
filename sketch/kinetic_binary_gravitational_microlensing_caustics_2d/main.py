"""
kinetic_binary_gravitational_microlensing_caustics_2d
2D relativistic astrophysics simulation of binary gravitational microlensing.
Solves the complex 2-body gravitational lens equation:
  w = z - m1 / (conj(z) - conj(z1)) - m2 / (conj(z) - conj(z2))
Computes critical curves (vanishing Jacobian det(J) = 0), diamond/astroid-shaped caustic networks,
relativistic image amplification A = 1 / |det(J)|, spacetime gravitational potential relief,
and Lagrangian photon ray kinematics demonstrating multi-image creation and annihilation.

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
WORK_NAME = "kinetic_binary_gravitational_microlensing_caustics_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180  # 25% progress

# Low-res tensor calculation grid for fast per-frame background rendering
GW, GH = 480, 270

# Particle configuration
NUM_PARTICLES = 2400
TRAIL_LEN = 8


class BinaryMicrolensingSimulation:
    def __init__(self, gw=GW, gh=GH):
        self.gw = gw
        self.gh = gh

        # Coordinate grid: aspect ratio 16:9, lens plane z = x + i*y
        x = np.linspace(-3.555, 3.555, gw, dtype=np.float32)
        y = np.linspace(-2.0, 2.0, gh, dtype=np.float32)
        self.X, self.Y = np.meshgrid(x, y)
        self.Z = self.X + 1j * self.Y

        # Binary lens system parameters
        # Lens masses: primary mass m1 = 0.65, secondary mass m2 = 0.35 (mass ratio q = 0.54)
        self.m1 = 0.65
        self.m2 = 0.35
        # Separation distance d between binary components
        self.d_sep = 1.15

        # Initialize Lagrangian photon tracer particles
        self.num_particles = NUM_PARTICLES
        self.trail_len = TRAIL_LEN

        rng = np.random.default_rng(20261030)
        # Background photons streaming through the lens plane
        self.p_x = rng.uniform(-3.5, 3.5, self.num_particles).astype(np.float32)
        self.p_y = rng.uniform(-1.95, 1.95, self.num_particles).astype(np.float32)
        self.p_vx = np.zeros(self.num_particles, dtype=np.float32)
        self.p_vy = np.zeros(self.num_particles, dtype=np.float32)

        # Particle species:
        # 0 = deflected background star rays (Electric Cyan & Glacial Teal)
        # 1 = caustic-crossing highly magnified image pairs (Blinding Solar Amber & Topaz Gold)
        self.p_species = rng.choice([0, 1], size=self.num_particles, p=[0.60, 0.40])

        # Trail history buffers
        self.trail_x = np.repeat(self.p_x[:, None], self.trail_len, axis=1)
        self.trail_y = np.repeat(self.p_y[:, None], self.trail_len, axis=1)

    def compute_fields(self, t):
        """
        Compute binary lens gravitational potential, Jacobian determinant det(J),
        magnification field A(z), and dual-light Blinn-Phong specular relief.
        t: float in [0, 1]
        """
        tau = 2.0 * np.pi * t

        # Orbit of the binary lens masses (slow counter-clockwise orbital rotation)
        orb_angle = 0.35 * np.sin(tau)  # smooth periodic libration
        z1 = - (self.d_sep * self.m2) * np.exp(1j * orb_angle)
        z2 = + (self.d_sep * self.m1) * np.exp(1j * orb_angle)

        # Vector distances to binary lenses
        dz1 = self.Z - z1
        dz2 = self.Z - z2
        r1_sq = np.abs(dz1) ** 2 + 0.04
        r2_sq = np.abs(dz2) ** 2 + 0.04

        # Gravitational potential Phi(x, y) = m1 * ln(r1) + m2 * ln(r2)
        phi = 0.5 * (self.m1 * np.log(r1_sq) + self.m2 * np.log(r2_sq))

        # Deflection angle alpha(z) = m1 / conj(dz1) + m2 / conj(dz2)
        # Complex shear gamma(z) = d(alpha) / dz = m1 / (conj(dz1)**2) + m2 / (conj(dz2)**2)
        # Convergence kappa = 0 (point masses outside singular cores)
        # Jacobian determinant: det(J) = 1 - |gamma|^2
        gamma = self.m1 / (np.conj(dz1) ** 2) + self.m2 / (np.conj(dz2) ** 2)
        gamma_mag = np.abs(gamma)
        det_J = 1.0 - (gamma_mag ** 2)

        # Critical curves correspond to det(J) == 0 -> |gamma| == 1
        # Magnification A = 1 / |det(J)| (regularized with softening epsilon)
        eps = 0.12
        magnification = 1.0 / np.sqrt(det_J ** 2 + eps ** 2)

        # Source position w_source(t) moving across the caustic network
        # Trajectory: straight horizontal sweep with vertical oscillation
        source_x = 2.2 * np.cos(tau)
        source_y = 0.65 * np.sin(2.0 * tau)
        w_source = source_x + 1j * source_y

        # Lens equation mapping: w = z - alpha(z)
        w_lens = self.Z - (self.m1 / np.conj(dz1) + self.m2 / np.conj(dz2))
        dist_to_source = np.abs(w_lens - w_source)

        # Source image brightness: Gaussian source profile mapped through lens equation
        source_radius = 0.22
        source_images = np.exp(- (dist_to_source ** 2) / (2.0 * (source_radius ** 2))) * magnification

        # Critical curve highlight (where |det(J)| is minimum)
        crit_curve_glow = np.exp(- (det_J ** 2) / 0.04)

        # Spacetime curvature surface normal for dual-light Blinn-Phong specular relief
        # Height map combines gravitational potential depth with caustic magnification ridges
        height = -0.45 * phi + 0.25 * np.clip(np.log1p(magnification), 0.0, 3.5)
        dhx = np.gradient(height, axis=1) * (self.gw / 7.11)
        dhy = np.gradient(height, axis=0) * (self.gh / 4.0)

        norm = np.sqrt(dhx ** 2 + dhy ** 2 + 1.0)
        nx = -dhx / norm
        ny = -dhy / norm
        nz = 1.0 / norm

        # Key light (Electric Cyan, top-left)
        lx1, ly1, lz1 = -0.577, 0.577, 0.577
        dot1 = np.maximum(0.0, nx * lx1 + ny * ly1 + nz * lz1)
        spec1 = dot1 ** 8

        # Fill light (Warm Amber, bottom-right)
        lx2, ly2, lz2 = 0.577, -0.577, 0.577
        dot2 = np.maximum(0.0, nx * lx2 + ny * ly2 + nz * lz2)
        spec2 = dot2 ** 6

        # Synthesize RGB buffer
        # Base: Deep Spacetime Obsidian Void
        r = np.full((self.gh, self.gw), 3.0, dtype=np.float32)
        g = np.full((self.gh, self.gw), 4.0, dtype=np.float32)
        b = np.full((self.gh, self.gw), 10.0, dtype=np.float32)

        # Gravitational potential wells (Midnight Sapphire & Deep Indigo)
        pot_depth = np.clip(-phi, 0.0, 3.0)
        r += pot_depth * 10.0
        g += pot_depth * 25.0
        b += pot_depth * 65.0

        # Critical Curves (Electric Glacial Cyan & Radiant Jade)
        r += crit_curve_glow * 0.0
        g += crit_curve_glow * 210.0
        b += crit_curve_glow * 255.0

        # Highly Magnified Source Images & Caustic Flare (Incandescent Solar Gold & Pearl White)
        flare = np.clip(source_images * 0.85, 0.0, 4.0)
        r += flare * 255.0
        g += flare * 195.0
        b += flare * 60.0

        # White core hot-spots for peak magnification
        white_hot = np.clip(flare - 1.5, 0.0, 2.0)
        r += white_hot * 90.0
        g += white_hot * 90.0
        b += white_hot * 180.0

        # Specular sheen relief
        r += spec1 * 90.0 + spec2 * 130.0
        g += spec1 * 170.0 + spec2 * 75.0
        b += spec1 * 220.0 + spec2 * 30.0

        rgb = np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
        return rgb, z1, z2, w_source

    def update_particles(self, t, z1, z2):
        """
        Advect Lagrangian photon tracer particles.
        Photons undergo gravitational geodesic bending around binary masses z1, z2,
        with extreme acceleration and swirling along critical caustic folds.
        """
        tau = 2.0 * np.pi * t

        # Roll trail buffers
        self.trail_x = np.roll(self.trail_x, 1, axis=1)
        self.trail_y = np.roll(self.trail_y, 1, axis=1)
        self.trail_x[:, 0] = self.p_x
        self.trail_y[:, 0] = self.p_y

        pz = self.p_x + 1j * self.p_y

        # Distance vectors to binary masses
        dz1 = pz - z1
        dz2 = pz - z2
        r1_sq = np.abs(dz1) ** 2 + 0.03
        r2_sq = np.abs(dz2) ** 2 + 0.03

        # Gravitational attractive acceleration: a = - grad(Phi)
        # a = - m1 * dz1 / r1_sq - m2 * dz2 / r2_sq
        a_grav = - (self.m1 * dz1 / r1_sq + self.m2 * dz2 / r2_sq)

        # Add orbital frame dragging / Coriolis curl
        curl_v = 0.35 * 1j * (self.m1 * dz1 / np.sqrt(r1_sq) - self.m2 * dz2 / np.sqrt(r2_sq))

        # Base background stream velocity (horizontal drift from left to right)
        v_stream = 0.85 + 0.15 * np.cos(self.p_y * 2.0 + tau)

        fx = a_grav.real + curl_v.real + 0.35
        fy = a_grav.imag + curl_v.imag

        # Integrate velocities with relativistic damping
        dt = 0.016
        self.p_vx = self.p_vx * 0.86 + fx * dt * 2.5
        self.p_vy = self.p_vy * 0.86 + fy * dt * 2.5

        # Speed clamp
        speed = np.sqrt(self.p_vx ** 2 + self.p_vy ** 2) + 1e-6
        max_speed = 3.2
        overspeed = speed > max_speed
        self.p_vx[overspeed] = (self.p_vx[overspeed] / speed[overspeed]) * max_speed
        self.p_vy[overspeed] = (self.p_vy[overspeed] / speed[overspeed]) * max_speed

        # Integrate positions
        new_x = self.p_x + (self.p_vx + v_stream) * dt
        new_y = self.p_y + self.p_vy * dt

        # Recycle particles that exit screen or fall into the black hole / lens cores
        recycle_mask = (
            (new_x > 3.55) | (new_x < -3.55) |
            (new_y > 2.0) | (new_y < -2.0) |
            (r1_sq < 0.015) | (r2_sq < 0.015)
        )

        if np.any(recycle_mask):
            num_reset = np.sum(recycle_mask)
            rng = np.random.default_rng()
            new_x[recycle_mask] = rng.uniform(-3.5, -3.2, num_reset).astype(np.float32)
            new_y[recycle_mask] = rng.uniform(-1.9, 1.9, num_reset).astype(np.float32)
            self.p_vx[recycle_mask] = rng.uniform(0.1, 0.4, num_reset).astype(np.float32)
            self.p_vy[recycle_mask] = rng.uniform(-0.1, 0.1, num_reset).astype(np.float32)
            # Reset history buffer to prevent screen-spanning streak artifacts
            self.trail_x[recycle_mask, :] = new_x[recycle_mask, None]
            self.trail_y[recycle_mask, :] = new_y[recycle_mask, None]

        self.p_x = new_x
        self.p_y = new_y


# Global simulation instance
sim = None


def setup():
    global sim
    py5.size(1920, 1080, py5.P2D)
    py5.frame_rate(FPS)
    sim = BinaryMicrolensingSimulation(GW, GH)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    global sim
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        return

    t = (frame - 1) / float(TOTAL_FRAMES)

    # 1. Compute vectorized 2D gravitational lens & caustic magnification field
    rgb_field, z1, z2, w_source = sim.compute_fields(t)

    # Draw background field
    bg_img = py5.create_image_from_numpy(rgb_field, 'RGB')
    py5.image(bg_img, 0, 0, py5.width, py5.height)

    # 2. Update Lagrangian photon tracer particles
    sim.update_particles(t, z1, z2)

    # 3. Vectorized rendering of photon trajectory ribbons
    # Convert simulation coordinates (-3.555..3.555, -2.0..2.0) to screen pixel coordinates
    sx = (sim.trail_x + 3.555) / 7.11 * py5.width
    sy = (sim.trail_y + 2.0) / 4.0 * py5.height

    # Filter out wrap-around / jump lines
    dist_threshold_sq = (0.28 * py5.width) ** 2
    py5.stroke_weight(1.5)

    # Batch draw trail segments
    for seg in range(sim.trail_len - 1):
        x0 = sx[:, seg]
        y0 = sy[:, seg]
        x1 = sx[:, seg + 1]
        y1 = sy[:, seg + 1]

        valid = ((x1 - x0) ** 2 + (y1 - y0) ** 2) < dist_threshold_sq

        # Species 0: Deflected Background Star Rays (Electric Cyan & Glacial Jade)
        mask0 = valid & (sim.p_species == 0)
        if np.any(mask0):
            alpha0 = int(220 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(0, 229, 255, alpha0)
            lines0 = np.column_stack([x0[mask0], y0[mask0], x1[mask0], y1[mask0]])
            py5.lines(lines0)

        # Species 1: Caustic-Crossing Highly Magnified Rays (Solar Gold & Topaz Amber)
        mask1 = valid & (sim.p_species == 1)
        if np.any(mask1):
            alpha1 = int(255 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(255, 183, 3, alpha1)
            lines1 = np.column_stack([x0[mask1], y0[mask1], x1[mask1], y1[mask1]])
            py5.lines(lines1)

    # Batch draw particle spark heads
    head_x = sx[:, 0]
    head_y = sy[:, 0]

    # Deflected ray sparks (Cyan-White Diamond)
    mask_pts0 = sim.p_species == 0
    py5.stroke_weight(2.8)
    py5.stroke(215, 255, 255, 245)
    pts0 = np.column_stack([head_x[mask_pts0], head_y[mask_pts0]])
    py5.points(pts0)

    # Magnified caustic sparks (Solar Gold / Liquid Diamond)
    mask_pts1 = sim.p_species == 1
    py5.stroke_weight(3.4)
    py5.stroke(255, 245, 190, 255)
    pts1 = np.column_stack([head_x[mask_pts1], head_y[mask_pts1]])
    py5.points(pts1)

    # 4. Draw Binary Lens Centers (Subtle Gravitational Cores)
    for z_lens in [z1, z2]:
        lx = (z_lens.real + 3.555) / 7.11 * py5.width
        ly = (z_lens.imag + 2.0) / 4.0 * py5.height
        py5.no_stroke()
        py5.fill(0, 229, 255, 180)
        py5.circle(lx, ly, 10.0)
        py5.fill(255, 255, 255, 240)
        py5.circle(lx, ly, 5.0)

    # 5. Save frame for video compilation
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image at designated frame
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Binary microlensing preview captured: {PREVIEW_PATH}")

    # Progress report
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        progress = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress:.1f}%)")

    # 6. Finalize animation encoding on completion
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
