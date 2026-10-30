"""
kinetic_non_hermitian_exceptional_point_caustics_2d
2D non-Hermitian wave physics and singular photonics simulation.
Models parity-time (PT) symmetric coupled optical waveguides with balanced gain (+i*gamma)
and loss (-i*gamma). Demonstrates PT-symmetry breaking, coalescence of eigenvalues and eigenvectors
at an Exceptional Point (EP, gamma = kappa), two-sheeted Riemann surface branch cut caustics,
and chiral unidirectional photon amplification.

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
WORK_NAME = "kinetic_non_hermitian_exceptional_point_caustics_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180  # 25% progress

# Low-res computational tensor grid for fast 4K background synthesis
GW, GH = 480, 270

# Particle configuration
NUM_PARTICLES = 2400
TRAIL_LEN = 8


class NonHermitianEPSimulation:
    def __init__(self, gw=GW, gh=GH):
        self.gw = gw
        self.gh = gh

        # Coordinate grid: aspect ratio 16:9, centered at origin
        x = np.linspace(-3.555, 3.555, gw, dtype=np.float32)
        y = np.linspace(-2.0, 2.0, gh, dtype=np.float32)
        self.X, self.Y = np.meshgrid(x, y)

        # Coupled waveguide geometry:
        # Gain guide centered at y = +0.70
        # Loss guide centered at y = -0.70
        self.y_gain = 0.70
        self.y_loss = -0.70
        self.guide_width = 0.38

        # Spatial envelopes of the waveguides
        self.env_gain = np.exp(- ((self.Y - self.y_gain) ** 2) / (2.0 * (self.guide_width ** 2)))
        self.env_loss = np.exp(- ((self.Y - self.y_loss) ** 2) / (2.0 * (self.guide_width ** 2)))
        self.coupling_zone = np.exp(- (self.Y ** 2) / (2.0 * (0.55 ** 2)))

        # Coupling strength kappa and gain/loss rate gamma
        self.kappa_base = 1.0

        # Initialize Lagrangian photon quasiparticles
        self.num_particles = NUM_PARTICLES
        self.trail_len = TRAIL_LEN

        rng = np.random.default_rng(20261030)
        # Half initialized in gain waveguide, half in loss waveguide
        half = self.num_particles // 2
        self.p_species = np.array([0] * half + [1] * half, dtype=np.int32)

        # X positions spread along propagation direction
        self.p_x = rng.uniform(-3.5, 3.5, self.num_particles).astype(np.float32)
        # Y positions clustered inside the waveguides
        self.p_y = np.zeros(self.num_particles, dtype=np.float32)
        self.p_y[:half] = self.y_gain + rng.normal(0, 0.12, half).astype(np.float32)
        self.p_y[half:] = self.y_loss + rng.normal(0, 0.12, half).astype(np.float32)

        self.p_vx = np.zeros(self.num_particles, dtype=np.float32)
        self.p_vy = np.zeros(self.num_particles, dtype=np.float32)

        # Trail history buffers
        self.trail_x = np.repeat(self.p_x[:, None], self.trail_len, axis=1)
        self.trail_y = np.repeat(self.p_y[:, None], self.trail_len, axis=1)

    def compute_fields(self, t):
        """
        Compute non-Hermitian 2D wave fields:
        1. Encircling the Exceptional Point: gamma(t) = kappa * (1.0 + 0.85 * sin(2*pi*t))
        2. Eigenvalue splitting / coalescence: Delta_lambda = sqrt(kappa^2 - gamma^2)
        3. Real & Imaginary optical field intensity textures with branch cuts.
        4. Dual-light Blinn-Phong specular relief normal mapping.
        """
        tau = 2.0 * np.pi * t

        # Dynamic gain/loss modulation sweeping through the Exceptional Point (EP at ratio = 1.0)
        # When gamma < kappa: PT-symmetric phase (real eigenvalues, oscillatory beating)
        # When gamma > kappa: Broken PT phase (complex conjugate eigenvalues, exponential growth/decay)
        ep_param = np.sin(tau)  # parameter in [-1, +1]
        gamma = self.kappa_base * (1.0 + 0.85 * ep_param)
        kappa = self.kappa_base

        # Eigenvalue discriminant: D = kappa^2 - gamma^2
        # Near EP (D = 0), square root singularity sqrt(D) generates Riemann sheet topology
        D = kappa ** 2 - gamma ** 2
        det_sign = np.sign(D)
        abs_D = np.abs(D)

        # Spatial beating frequency along propagation axis X
        k_beat = np.sqrt(abs_D) * 3.5
        phase_x = 4.0 * self.X - 2.0 * tau

        # Wavefunction in Gain guide: amp_gain(x, t)
        if D >= 0:
            # Exact PT-symmetric regime: harmonic Rabi oscillations between channels
            amp_gain = np.cos(k_beat * self.X - tau)
            amp_loss = np.sin(k_beat * self.X - tau)
        else:
            # Broken PT regime: exponential amplification in gain, suppression in loss
            amp_gain = np.cosh(k_beat * (self.X * 0.25)) * np.cos(phase_x)
            amp_loss = np.sinh(k_beat * (self.X * 0.25)) * np.sin(phase_x)

        field_gain = (amp_gain ** 2) * self.env_gain
        field_loss = (amp_loss ** 2) * self.env_loss

        # Exceptional Point Singularity Ribbon: localized along coupling interface Y ~ 0
        # Characterized by 2D Riemann sheet branch cut vortex caustics
        ep_proximity = np.exp(- (D ** 2) / 0.15)
        caustic_vortex = np.sin(6.0 * self.X - 3.0 * tau) * np.cos(8.0 * self.Y + tau)
        ep_ribbon = ep_proximity * self.coupling_zone * (0.8 + 0.5 * caustic_vortex)

        # Total photonic field intensity
        intensity = 1.6 * field_gain + 0.9 * field_loss + 1.8 * ep_ribbon

        # Spacetime / dielectric normal relief mapping
        ddx = np.gradient(intensity, axis=1) * (self.gw / 7.11)
        ddy = np.gradient(intensity, axis=0) * (self.gh / 4.0)

        norm = np.sqrt(ddx ** 2 + ddy ** 2 + 1.0)
        nx = -ddx / norm
        ny = -ddy / norm
        nz = 1.0 / norm

        # Key light (Electric Cyan, top-left)
        lx1, ly1, lz1 = -0.577, 0.577, 0.577
        dot1 = np.maximum(0.0, nx * lx1 + ny * ly1 + nz * lz1)
        spec1 = dot1 ** 8

        # Fill light (Incandescent Coral, bottom-right)
        lx2, ly2, lz2 = 0.577, -0.577, 0.577
        dot2 = np.maximum(0.0, nx * lx2 + ny * ly2 + nz * lz2)
        spec2 = dot2 ** 6

        # Synthesize RGB buffer
        # Base: Deep Obsidian Glass Void
        r = np.full((self.gh, self.gw), 3.0, dtype=np.float32)
        g = np.full((self.gh, self.gw), 5.0, dtype=np.float32)
        b = np.full((self.gh, self.gw), 12.0, dtype=np.float32)

        # Gain Waveguide (Blinding Incandescent Neon Coral & Solar Amber)
        r += field_gain * 255.0
        g += field_gain * 95.0
        b += field_gain * 35.0

        # Loss Waveguide (Midnight Indigo & Actinic Royal Amethyst)
        r += field_loss * 110.0
        g += field_loss * 30.0
        b += field_loss * 215.0

        # Exceptional Point Singularity Ribbons (Radiant Glacial Cyan & Electric Mint)
        r += ep_ribbon * 10.0
        g += ep_ribbon * 245.0
        b += ep_ribbon * 220.0

        # Coalescence hot-spots (Liquid Diamond White)
        hotspots = np.clip(ep_ribbon * field_gain - 0.7, 0.0, 2.0)
        r += hotspots * 180.0
        g += hotspots * 220.0
        b += hotspots * 255.0

        # Specular sheen relief
        r += spec1 * 100.0 + spec2 * 140.0
        g += spec1 * 190.0 + spec2 * 70.0
        b += spec1 * 210.0 + spec2 * 40.0

        rgb = np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
        return rgb, gamma, ep_proximity

    def update_particles(self, t, gamma, ep_proximity):
        """
        Advect Lagrangian photon quasiparticles.
        Photons undergo coherent tunnel-coupling between the gain and loss guides.
        Near the Exceptional Point (ep_proximity ~ 1), tunneling becomes non-reciprocal:
        photons in the loss guide are channeled unidirectionally into the gain guide,
        accelerating with high forward momentum.
        """
        tau = 2.0 * np.pi * t

        # Roll trail buffers
        self.trail_x = np.roll(self.trail_x, 1, axis=1)
        self.trail_y = np.roll(self.trail_y, 1, axis=1)
        self.trail_x[:, 0] = self.p_x
        self.trail_y[:, 0] = self.p_y

        # Forward propagation speed (optical group velocity along +X)
        v_group = 1.35 + 0.45 * ep_proximity * (self.p_species == 0)

        # Vertical restoring force confining particles to waveguide channels
        # Target Y: gain guide (+0.70) or loss guide (-0.70)
        target_y = np.where(self.p_species == 0, self.y_gain, self.y_loss)

        # Tunnel-coupling exchange: periodic hopping between channels
        # In exact PT phase, symmetric Rabi flopping; near EP, asymmetric transfer to gain channel
        hop_prob = 0.035 * (1.0 + 1.2 * ep_proximity)
        rng = np.random.default_rng()
        switches = rng.uniform(0.0, 1.0, self.num_particles) < hop_prob

        # Chiral bias: at EP, loss particles flip to gain with 85% probability
        if ep_proximity > 0.5:
            switches_to_gain = switches & (self.p_species == 1)
            self.p_species[switches_to_gain] = 0
            # Reduced probability of going from gain to loss
            switches_to_loss = switches & (self.p_species == 0) & (rng.uniform(0.0, 1.0, self.num_particles) < 0.2)
            self.p_species[switches_to_loss] = 1
        else:
            self.p_species[switches] = 1 - self.p_species[switches]

        # Waveguide confinement force + Rabi coupling vertical acceleration
        fy = (target_y - self.p_y) * 4.5 + 0.35 * np.sin(4.0 * self.p_x - tau)

        # Integrate velocities with damping
        dt = 0.016
        self.p_vx = self.p_vx * 0.85 + v_group * 0.15
        self.p_vy = self.p_vy * 0.80 + fy * dt

        # Speed clamp
        speed = np.sqrt(self.p_vx ** 2 + self.p_vy ** 2) + 1e-6
        max_speed = 3.5
        overspeed = speed > max_speed
        self.p_vx[overspeed] = (self.p_vx[overspeed] / speed[overspeed]) * max_speed
        self.p_vy[overspeed] = (self.p_vy[overspeed] / speed[overspeed]) * max_speed

        # Integrate positions
        new_x = self.p_x + self.p_vx * dt * 2.8
        new_y = self.p_y + self.p_vy * dt

        # Recycle particles that exit the right boundary (wrap to left)
        wrap_mask = new_x > 3.55
        if np.any(wrap_mask):
            num_wrap = np.sum(wrap_mask)
            rng_wrap = np.random.default_rng()
            new_x[wrap_mask] = rng_wrap.uniform(-3.55, -3.35, num_wrap).astype(np.float32)
            # Reassign to waveguides
            new_species = rng_wrap.choice([0, 1], size=num_wrap, p=[0.6, 0.4])
            self.p_species[wrap_mask] = new_species
            new_y[wrap_mask] = np.where(new_species == 0, self.y_gain, self.y_loss) + rng_wrap.normal(0, 0.1, num_wrap).astype(np.float32)
            self.p_vx[wrap_mask] = rng_wrap.uniform(1.2, 1.6, num_wrap).astype(np.float32)
            self.p_vy[wrap_mask] = 0.0
            # Reset history buffer to prevent screen-spanning streak artifacts
            self.trail_x[wrap_mask, :] = new_x[wrap_mask, None]
            self.trail_y[wrap_mask, :] = new_y[wrap_mask, None]

        self.p_x = new_x
        self.p_y = new_y


# Global simulation instance
sim = None


def setup():
    global sim
    py5.size(1920, 1080, py5.P2D)
    py5.frame_rate(FPS)
    sim = NonHermitianEPSimulation(GW, GH)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    global sim
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        return

    t = (frame - 1) / float(TOTAL_FRAMES)

    # 1. Compute vectorized 2D non-Hermitian & specular field
    rgb_field, gamma, ep_proximity = sim.compute_fields(t)

    # Draw background field
    bg_img = py5.create_image_from_numpy(rgb_field, 'RGB')
    py5.image(bg_img, 0, 0, py5.width, py5.height)

    # 2. Update Lagrangian photon quasiparticles
    sim.update_particles(t, gamma, ep_proximity)

    # 3. Vectorized rendering of photon trajectory ribbons
    # Convert simulation coordinates (-3.555..3.555, -2.0..2.0) to screen pixel coordinates
    sx = (sim.trail_x + 3.555) / 7.11 * py5.width
    sy = (sim.trail_y + 2.0) / 4.0 * py5.height

    # Filter out wrap-around lines
    dist_threshold_sq = (0.28 * py5.width) ** 2
    py5.stroke_weight(1.6)

    # Batch draw trail segments
    for seg in range(sim.trail_len - 1):
        x0 = sx[:, seg]
        y0 = sy[:, seg]
        x1 = sx[:, seg + 1]
        y1 = sy[:, seg + 1]

        valid = ((x1 - x0) ** 2 + (y1 - y0) ** 2) < dist_threshold_sq

        # Gain channel particles (Neon Coral & Molten Solar Amber)
        mask0 = valid & (sim.p_species == 0)
        if np.any(mask0):
            alpha0 = int(240 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(255, 110, 40, alpha0)
            lines0 = np.column_stack([x0[mask0], y0[mask0], x1[mask0], y1[mask0]])
            py5.lines(lines0)

        # Loss channel particles (Royal Amethyst & Electric Violet)
        mask1 = valid & (sim.p_species == 1)
        if np.any(mask1):
            alpha1 = int(220 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(147, 51, 234, alpha1)
            lines1 = np.column_stack([x0[mask1], y0[mask1], x1[mask1], y1[mask1]])
            py5.lines(lines1)

    # Batch draw particle spark heads
    head_x = sx[:, 0]
    head_y = sy[:, 0]

    # Gain sparks (Solar White / Incandescent Coral)
    mask_pts0 = sim.p_species == 0
    py5.stroke_weight(3.2)
    py5.stroke(255, 235, 190, 255)
    pts0 = np.column_stack([head_x[mask_pts0], head_y[mask_pts0]])
    py5.points(pts0)

    # Loss sparks (Radiant Amethyst / Ice Magenta)
    mask_pts1 = sim.p_species == 1
    py5.stroke_weight(2.8)
    py5.stroke(215, 180, 255, 240)
    pts1 = np.column_stack([head_x[mask_pts1], head_y[mask_pts1]])
    py5.points(pts1)

    # 4. Save frame for video compilation
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image at designated frame
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Non-Hermitian EP preview captured: {PREVIEW_PATH}")

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
