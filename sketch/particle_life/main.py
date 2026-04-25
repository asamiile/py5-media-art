from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Emergent society" — five types of particles governed by a random attraction/
# repulsion matrix; simple pairwise forces produce emergent clusters, membranes,
# predator-prey orbits, and self-organizing patterns reminiscent of living cells.

N_TYPES  = 5
N_EACH   = 200     # particles per type
N        = N_TYPES * N_EACH

R_MIN    = 20.0    # universal short-range repulsion radius
R_MAX    = 100.0   # interaction cutoff
MAX_REP  = 1.5     # max repulsion force magnitude
FRICTION = 0.82    # velocity damping per step
DT       = 0.6
N_STEPS  = 250     # simulation steps before rendering

PARTICLE_R = 12.0  # display circle radius
ALPHA      = 175   # circle fill alpha

W, H = SIZE

# Particle type colors: crimson, gold, teal, violet, sage
COLORS = [
    (210,  55,  65),   # crimson
    (225, 182,  52),   # gold
    ( 52, 185, 185),   # teal
    (155,  55, 222),   # violet
    (122, 205, 108),   # sage green
]


def setup():
    py5.size(*SIZE)
    py5.background(6, 5, 10)

    rng = np.random.default_rng()

    # Random force matrix (N_TYPES × N_TYPES) — signed attraction/repulsion
    force_matrix = rng.uniform(-1.0, 1.0, (N_TYPES, N_TYPES)).astype(np.float32)

    # Initial positions and velocities
    types = np.repeat(np.arange(N_TYPES), N_EACH)
    pos = rng.uniform([0, 0], [W, H], (N, 2)).astype(np.float32)
    vel = np.zeros((N, 2), dtype=np.float32)

    # Simulation loop
    for _ in range(N_STEPS):
        # Pairwise differences: diff[i,j] = pos[j] - pos[i]
        diff = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]   # (N, N, 2)
        # Handle wrapping on the torus
        diff -= np.round(diff / [W, H]) * [W, H]

        dist2 = (diff ** 2).sum(axis=2) + 1e-6   # (N, N)
        dist  = np.sqrt(dist2)

        # Type-pair force strengths (N, N)
        f_strength = force_matrix[types[:, np.newaxis], types[np.newaxis, :]]

        # Force profile: quadratic peak in ring [R_MIN, R_MAX]
        t_ring  = np.clip((dist - R_MIN) / (R_MAX - R_MIN), 0.0, 1.0)
        profile = f_strength * 4.0 * t_ring * (1.0 - t_ring)   # 0 outside ring

        # Short-range universal repulsion (overrides ring force for d < R_MIN)
        repulse = np.where(dist < R_MIN, -MAX_REP * (1.0 - dist / R_MIN), 0.0)
        profile += repulse

        # Zero self-force
        np.fill_diagonal(profile, 0.0)

        # Unit direction (toward pos[j])
        unit = diff / dist[:, :, np.newaxis]   # (N, N, 2)
        forces = (profile[:, :, np.newaxis] * unit).sum(axis=1)   # (N, 2)

        vel = vel * FRICTION + forces * DT
        pos = (pos + vel) % [W, H]   # wrap

    # --- Render final state ---
    py5.no_stroke()
    for ti in range(N_TYPES):
        col = COLORS[ti]
        py5.fill(*col, ALPHA)
        mask = types == ti
        for px, py_val in pos[mask]:
            if 0 <= px < W and 0 <= py_val < H:
                py5.circle(float(px), float(py_val), PARTICLE_R * 2)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()
