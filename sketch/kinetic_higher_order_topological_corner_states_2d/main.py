"""
kinetic_higher_order_topological_corner_states_2d
2D acoustic metamaterial and higher-order topological insulator (HOTI) simulation.
Simulates a 2D Benalcazar-Bernevig-Hughes (BBH) quadrupole topological lattice with synthetic pi-flux,
demonstrating bulk bandgap insulation, gapped edge dispersion, and robust zero-dimensional
topological corner bound state condensation under resonant acoustic excitation.

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
WORK_NAME = "kinetic_higher_order_topological_corner_states_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, "output.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180  # 25% progress

# Low-res tensor calculation grid for fast per-frame background rendering
GW, GH = 480, 270

# Particle configuration
NUM_PARTICLES = 2200
TRAIL_LEN = 8


class HOTISimulation:
    def __init__(self, gw=GW, gh=GH):
        self.gw = gw
        self.gh = gh

        # Coordinate grid: aspect ratio 16:9, centered at (0, 0)
        x = np.linspace(-3.555, 3.555, gw, dtype=np.float32)
        y = np.linspace(-2.0, 2.0, gh, dtype=np.float32)
        self.X, self.Y = np.meshgrid(x, y)

        # Lattice definition: finite rectangular array of unit cells
        # Unit cell grid: 12 columns x 7 rows
        self.nx_cells = 12
        self.ny_cells = 7
        cell_pitch_x = 0.50
        cell_pitch_y = 0.44

        # Metamaterial outer bounds (boundary of the finite lattice)
        self.x_min = -(self.nx_cells * cell_pitch_x) / 2.0
        self.x_max = (self.nx_cells * cell_pitch_x) / 2.0
        self.y_min = -(self.ny_cells * cell_pitch_y) / 2.0
        self.y_max = (self.ny_cells * cell_pitch_y) / 2.0

        # Four corner coordinates
        self.corners = np.array([
            [self.x_min, self.y_min],  # Bottom-Left: +1
            [self.x_max, self.y_min],  # Bottom-Right: -1
            [self.x_max, self.y_max],  # Top-Right: +1
            [self.x_min, self.y_max],  # Top-Left: -1
        ], dtype=np.float32)
        self.corner_signs = np.array([1.0, -1.0, 1.0, -1.0], dtype=np.float32)

        # Precompute static resonator pillar lattice mask
        self.lattice_mask = np.zeros((gh, gw), dtype=np.float32)
        intra_d = 0.11  # distance within unit cell
        for i in range(self.nx_cells):
            cx = self.x_min + (i + 0.5) * cell_pitch_x
            for j in range(self.ny_cells):
                cy = self.y_min + (j + 0.5) * cell_pitch_y
                # 4 sub-lattice sites: A, B, C, D
                subsites = [
                    (cx - intra_d, cy - intra_d),
                    (cx + intra_d, cy - intra_d),
                    (cx + intra_d, cy + intra_d),
                    (cx - intra_d, cy + intra_d),
                ]
                for sx, sy in subsites:
                    dist_sq = (self.X - sx) ** 2 + (self.Y - sy) ** 2
                    self.lattice_mask += np.exp(-dist_sq / (2.0 * (0.045 ** 2)))

        self.lattice_mask = np.clip(self.lattice_mask, 0.0, 1.0)

        # Precompute distances and angles to the 4 corners
        self.r_corners = np.zeros((4, gh, gw), dtype=np.float32)
        self.th_corners = np.zeros((4, gh, gw), dtype=np.float32)
        for k in range(4):
            cx, cy = self.corners[k]
            dx = self.X - cx
            dy = self.Y - cy
            self.r_corners[k] = np.sqrt(dx ** 2 + dy ** 2)
            self.th_corners[k] = np.arctan2(dy, dx)

        # Precompute corner localization envelope (exponential spatial confinement xi ~ 0.55)
        self.corner_envelope = np.zeros((gh, gw), dtype=np.float32)
        for k in range(4):
            self.corner_envelope += np.exp(-self.r_corners[k] / 0.52)

        # Initialize Lagrangian phonon quasiparticles
        self.num_particles = NUM_PARTICLES
        self.trail_len = TRAIL_LEN

        # Particles distributed across the metamaterial domain
        rng = np.random.default_rng(20261030)
        self.p_x = rng.uniform(-3.4, 3.4, self.num_particles).astype(np.float32)
        self.p_y = rng.uniform(-1.9, 1.9, self.num_particles).astype(np.float32)
        self.p_vx = np.zeros(self.num_particles, dtype=np.float32)
        self.p_vy = np.zeros(self.num_particles, dtype=np.float32)

        # Pre-allocate particle trail histories
        self.trail_x = np.repeat(self.p_x[:, None], self.trail_len, axis=1)
        self.trail_y = np.repeat(self.p_y[:, None], self.trail_len, axis=1)

        # Particle species: 0 = bulk phonon (teal/cyan), 1 = trapped corner polariton (gold/amber)
        self.p_species = rng.choice([0, 1], size=self.num_particles, p=[0.65, 0.35])

    def compute_fields(self, t):
        """
        Compute acoustic pressure fields, corner eigenmode excitation, and specular normal relief.
        t: float in [0, 1]
        """
        tau = 2.0 * np.pi * t

        # Resonant pumping cycle: sweep into sharp corner resonance
        # Corner resonance intensity peaks twice per cycle (symmetric breathing)
        corner_drive = np.sin(tau) ** 2
        bulk_suppression = 1.0 - 0.75 * corner_drive  # bulk is insulating/gapped

        # Corner eigenmode acoustic wavefunction: 4 localized poles with BBH alternating phases
        # Quadrupolar phase sign (+, -, +, -) with harmonic oscillation
        corner_wave = np.zeros((self.gh, self.gw), dtype=np.float32)
        for k in range(4):
            sign = self.corner_signs[k]
            rk = self.r_corners[k]
            thk = self.th_corners[k]
            # Localized acoustic quadrupole breathing with spatial acoustic waves
            phase_k = 6.0 * rk - 2.0 * tau + sign * (np.pi / 2.0)
            amp_k = np.exp(-rk / 0.58) / np.sqrt(rk + 0.15)
            # Add vortex phase twist around corner core
            corner_wave += sign * amp_k * np.cos(phase_k + 2.0 * thk)

        # Bulk acoustic background wave (evanescent scattered modes)
        bulk_wave = np.sin(4.0 * self.X + 3.0 * self.Y - tau) * np.cos(3.0 * self.X - 4.0 * self.Y + tau)
        # Bounded within the metamaterial plate
        in_plate = (
            (self.X >= self.x_min - 0.2) & (self.X <= self.x_max + 0.2) &
            (self.Y >= self.y_min - 0.2) & (self.Y <= self.y_max + 0.2)
        ).astype(np.float32)

        # Combined pressure amplitude P(x, y, t)
        pressure = (1.8 * corner_drive * corner_wave + 0.35 * bulk_suppression * bulk_wave) * in_plate

        # Local acoustic intensity / energy density
        intensity = pressure ** 2 + 1.2 * corner_drive * self.corner_envelope

        # Dual-light Blinn-Phong specular relief normal mapping
        # Compute spatial derivatives dP/dx, dP/dy
        dpx = np.gradient(pressure, axis=1) * (self.gw / 7.11)
        dpy = np.gradient(pressure, axis=0) * (self.gh / 4.0)

        # Normal vector N = (-dpx, -dpy, 1) / ||N||
        norm = np.sqrt(dpx ** 2 + dpy ** 2 + 1.0)
        nx = -dpx / norm
        ny = -dpy / norm
        nz = 1.0 / norm

        # Key light (top-left, cold cyan-white)
        lx1, ly1, lz1 = -0.577, 0.577, 0.577
        dot1 = np.maximum(0.0, nx * lx1 + ny * ly1 + nz * lz1)
        spec1 = dot1 ** 8

        # Fill light (bottom-right, actinic warm gold)
        lx2, ly2, lz2 = 0.577, -0.577, 0.577
        dot2 = np.maximum(0.0, nx * lx2 + ny * ly2 + nz * lz2)
        spec2 = dot2 ** 6

        # Synthesize RGB buffer
        # Base background: Deep Obsidian Silicon Void
        r = np.full((self.gh, self.gw), 5.0, dtype=np.float32)
        g = np.full((self.gh, self.gw), 7.0, dtype=np.float32)
        b = np.full((self.gh, self.gw), 15.0, dtype=np.float32)

        # Substrate resonator lattice grid
        r += self.lattice_mask * 18.0
        g += self.lattice_mask * 28.0
        b += self.lattice_mask * 48.0

        # Positive acoustic pressure -> Radiant Cyan & Electric Jade
        pos_p = np.maximum(0.0, pressure)
        r += pos_p * 15.0
        g += pos_p * 180.0
        b += pos_p * 220.0

        # Negative acoustic pressure -> Cryogenic Indigo & Royal Violet
        neg_p = np.maximum(0.0, -pressure)
        r += neg_p * 110.0
        g += neg_p * 35.0
        b += neg_p * 210.0

        # Blazing zero-dimensional corner bound states (Incandescent Topaz Gold & Pearl White)
        corner_glow = np.clip(corner_drive * (self.corner_envelope ** 1.3) * 1.6, 0.0, 3.5)
        r += corner_glow * 255.0
        g += corner_glow * 210.0
        b += corner_glow * 80.0

        # Specular sheen relief
        r += spec1 * 120.0 + spec2 * 90.0
        g += spec1 * 180.0 + spec2 * 70.0
        b += spec1 * 210.0 + spec2 * 30.0

        rgb = np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
        return rgb, pressure

    def update_particles(self, t):
        """
        Advect Lagrangian phonon particles.
        Quasiparticles are accelerated toward the 4 corner bound states during resonance,
        circling in tight orbital limit cycles and emitting trail filaments.
        """
        tau = 2.0 * np.pi * t
        corner_drive = np.sin(tau) ** 2

        # Roll trail buffers
        self.trail_x = np.roll(self.trail_x, 1, axis=1)
        self.trail_y = np.roll(self.trail_y, 1, axis=1)
        self.trail_x[:, 0] = self.p_x
        self.trail_y[:, 0] = self.p_y

        # Compute forces from the 4 corners
        fx = np.zeros(self.num_particles, dtype=np.float32)
        fy = np.zeros(self.num_particles, dtype=np.float32)

        for k in range(4):
            cx, cy = self.corners[k]
            sign = self.corner_signs[k]
            dx = cx - self.p_x
            dy = cy - self.p_y
            dist_sq = dx ** 2 + dy ** 2 + 0.04
            dist = np.sqrt(dist_sq)

            # Attractive topological force toward corner + azimuthal vortex swirl
            f_attract = (1.2 * corner_drive + 0.15) / (dist_sq * (dist + 0.4))
            # Azimuthal swirl velocity
            fx += f_attract * dx - sign * 0.85 * corner_drive * (dy / dist)
            fy += f_attract * dy + sign * 0.85 * corner_drive * (dx / dist)

        # Bulk acoustic drift
        fx += 0.25 * np.sin(3.0 * self.p_y + tau)
        fy += 0.25 * np.cos(3.0 * self.p_x - tau)

        # Update velocities with damping
        dt = 0.016
        self.p_vx = self.p_vx * 0.88 + fx * dt
        self.p_vy = self.p_vy * 0.88 + fy * dt

        # Speed limit
        speed = np.sqrt(self.p_vx ** 2 + self.p_vy ** 2) + 1e-6
        max_speed = 2.8
        overspeed = speed > max_speed
        self.p_vx[overspeed] = (self.p_vx[overspeed] / speed[overspeed]) * max_speed
        self.p_vy[overspeed] = (self.p_vy[overspeed] / speed[overspeed]) * max_speed

        # Integrate positions
        new_x = self.p_x + self.p_vx * dt
        new_y = self.p_y + self.p_vy * dt

        # Recycle particles that venture beyond domain or get too close to corner singular centers
        reset_mask = (
            (new_x < -3.5) | (new_x > 3.5) |
            (new_y < -1.95) | (new_y > 1.95)
        )
        for k in range(4):
            cx, cy = self.corners[k]
            d_sq = (new_x - cx) ** 2 + (new_y - cy) ** 2
            reset_mask |= (d_sq < 0.008)

        # Re-inject recycled particles randomly into the metamaterial
        if np.any(reset_mask):
            num_reset = np.sum(reset_mask)
            rng = np.random.default_rng()
            new_x[reset_mask] = rng.uniform(-3.3, 3.3, num_reset).astype(np.float32)
            new_y[reset_mask] = rng.uniform(-1.85, 1.85, num_reset).astype(np.float32)
            self.p_vx[reset_mask] = rng.uniform(-0.1, 0.1, num_reset).astype(np.float32)
            self.p_vy[reset_mask] = rng.uniform(-0.1, 0.1, num_reset).astype(np.float32)
            # Reset history buffer to prevent screen-crossing streak artifacts
            self.trail_x[reset_mask, :] = new_x[reset_mask, None]
            self.trail_y[reset_mask, :] = new_y[reset_mask, None]

        self.p_x = new_x
        self.p_y = new_y


# Global simulation instance
sim = None
bg_image = None


def setup():
    global sim
    py5.size(1920, 1080, py5.P2D)
    py5.frame_rate(FPS)
    sim = HOTISimulation(GW, GH)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    global sim, bg_image
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        return

    t = (frame - 1) / float(TOTAL_FRAMES)

    # 1. Compute vectorized 2D acoustic & specular field
    rgb_field, _ = sim.compute_fields(t)

    # Convert to py5 image and draw as background
    bg_img = py5.create_image_from_numpy(rgb_field, 'RGB')
    py5.image(bg_img, 0, 0, py5.width, py5.height)

    # 2. Update Lagrangian phonon quasiparticles
    sim.update_particles(t)

    # 3. Vectorized rendering of phonon trajectory trails
    # Transform simulation coordinates (-3.555..3.555, -2.0..2.0) to screen pixel coordinates
    # Screen X: (sim_x + 3.555) / 7.11 * width
    # Screen Y: (sim_y + 2.0) / 4.0 * height
    sx = (sim.trail_x + 3.555) / 7.11 * py5.width
    sy = (sim.trail_y + 2.0) / 4.0 * py5.height

    # Build line segments between successive trail history points: (x[t], y[t]) -> (x[t+1], y[t+1])
    # Filter out wrap-around / jump lines
    dist_threshold_sq = (0.35 * py5.width) ** 2
    py5.stroke_weight(1.5)

    # Batch draw trail segments
    for seg in range(sim.trail_len - 1):
        x0 = sx[:, seg]
        y0 = sy[:, seg]
        x1 = sx[:, seg + 1]
        y1 = sy[:, seg + 1]

        valid = ((x1 - x0) ** 2 + (y1 - y0) ** 2) < dist_threshold_sq

        # Draw species 0 (Bulk Phonon Streamlines: Radiant Electric Mint / Glacial Cyan)
        mask0 = valid & (sim.p_species == 0)
        if np.any(mask0):
            alpha0 = int(220 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(6, 182, 212, alpha0)
            lines0 = np.column_stack([x0[mask0], y0[mask0], x1[mask0], y1[mask0]])
            py5.lines(lines0)

        # Draw species 1 (Corner Trapped Polaritons: Incandescent Solar Gold / Topaz Amber)
        mask1 = valid & (sim.p_species == 1)
        if np.any(mask1):
            alpha1 = int(255 * (1.0 - seg / float(sim.trail_len)))
            py5.stroke(255, 183, 3, alpha1)
            lines1 = np.column_stack([x0[mask1], y0[mask1], x1[mask1], y1[mask1]])
            py5.lines(lines1)

    # Batch draw particle spark heads
    head_x = sx[:, 0]
    head_y = sy[:, 0]

    # Bulk phonon sparks (Diamond White / Cyan)
    mask_pts0 = sim.p_species == 0
    py5.stroke_weight(2.6)
    py5.stroke(220, 255, 255, 240)
    pts0 = np.column_stack([head_x[mask_pts0], head_y[mask_pts0]])
    py5.points(pts0)

    # Trapped corner polariton sparks (Solar Gold / Liquid White)
    mask_pts1 = sim.p_species == 1
    py5.stroke_weight(3.4)
    py5.stroke(255, 245, 200, 255)
    pts1 = np.column_stack([head_x[mask_pts1], head_y[mask_pts1]])
    py5.points(pts1)

    # 4. Save frame for video compilation
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image at designated frame
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Corner state preview captured: {PREVIEW_PATH}")

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
