from pathlib import Path
import py5
import numpy as np

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 1

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Fluid simulation parameters
GRID_SIZE = 100  # Simulation grid size (lower = faster, higher = more detailed)
ITERATIONS = 10  # Solver iterations
DT = 0.1  # Time step
DIFFUSION = 0.0001  # Diffusion rate
VISCOSITY = 0.0001  # Viscosity
VORTICITY_STRENGTH = 0.05  # Vorticity confinement strength

# Color palette
BACKGROUND = np.array([10, 22, 40], dtype=np.float64)  # Deep ocean navy
COLOR_CYAN = np.array([0, 212, 255], dtype=np.float64)  # Electric cyan
COLOR_CORAL = np.array([255, 107, 107], dtype=np.float64)  # Warm coral
COLOR_AMBER = np.array([255, 217, 61], dtype=np.float64)  # Golden amber

# Fluid fields
velocity_x = None
velocity_y = None
velocity_x_prev = None
velocity_y_prev = None
density = None
density_prev = None

def setup():
    global velocity_x, velocity_y, velocity_x_prev, velocity_y_prev
    global density, density_prev

    py5.size(*SIZE)
    py5.no_loop()

    # Initialize fluid fields
    velocity_x = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    velocity_y = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    velocity_x_prev = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    velocity_y_prev = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    density = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    density_prev = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)

    # Add initial sources
    add_sources()

    # Simulate for several steps to develop interesting patterns
    for _ in range(50):
        step()

def add_sources():
    """Add initial velocity and density sources"""
    global velocity_x, velocity_y, density

    # Add several swirling sources
    num_sources = 8
    for _ in range(num_sources):
        # Random position
        x = np.random.randint(10, GRID_SIZE - 10)
        y = np.random.randint(10, GRID_SIZE - 10)

        # Add velocity source (swirling motion)
        radius = 8
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < radius and dist > 0:
                        # Create swirling velocity
                        strength = 10.0 * (1 - dist/radius)
                        velocity_x[ny, nx] += -dy / dist * strength
                        velocity_y[ny, nx] += dx / dist * strength

        # Add density source
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < radius:
                        density[ny, nx] += 1.0 * (1 - dist/radius)

def step():
    """Perform one simulation step"""
    global velocity_x, velocity_y, velocity_x_prev, velocity_y_prev
    global density, density_prev

    # Add forces (random perturbations)
    if np.random.random() < 0.1:
        x = np.random.randint(5, GRID_SIZE - 5)
        y = np.random.randint(5, GRID_SIZE - 5)
        velocity_x[y, x] += np.random.uniform(-5, 5)
        velocity_y[y, x] += np.random.uniform(-5, 5)
        density[y, x] += 0.5

    # Velocity step
    diffuse(1, velocity_x_prev, velocity_x, VISCOSITY)
    diffuse(2, velocity_y_prev, velocity_y, VISCOSITY)

    project(velocity_x_prev, velocity_y_prev, velocity_x, velocity_y)

    advect(1, velocity_x, velocity_x_prev, velocity_x_prev, velocity_y_prev)
    advect(2, velocity_y, velocity_y_prev, velocity_x_prev, velocity_y_prev)

    project(velocity_x, velocity_y, velocity_x_prev, velocity_y_prev)

    # Density step
    diffuse(0, density_prev, density, DIFFUSION)
    advect(0, density, density_prev, velocity_x, velocity_y)

    # Apply vorticity confinement
    apply_vorticity_confinement()

def diffuse(b, x, x0, diff):
    """Solve diffusion equation using Gauss-Seidel relaxation"""
    a = DT * diff * (GRID_SIZE - 2) * (GRID_SIZE - 2)

    for _ in range(ITERATIONS):
        x[1:-1, 1:-1] = (x0[1:-1, 1:-1] + a * (
            x[0:-2, 1:-1] + x[2:, 1:-1] +
            x[1:-1, 0:-2] + x[1:-1, 2:]
        )) / (1 + 4 * a)

    set_bnd(b, x)

def advect(b, d, d0, u, v):
    """Advect field d along velocity field (u, v)"""
    dt0 = DT * (GRID_SIZE - 2)

    for j in range(1, GRID_SIZE - 1):
        for i in range(1, GRID_SIZE - 1):
            # Backtrace
            x = i - dt0 * u[j, i]
            y = j - dt0 * v[j, i]

            # Clamp to grid
            x = max(0.5, min(GRID_SIZE - 1.5, x))
            y = max(0.5, min(GRID_SIZE - 1.5, y))

            # Bilinear interpolation
            i0 = int(x)
            i1 = i0 + 1
            j0 = int(y)
            j1 = j0 + 1

            s1 = x - i0
            s0 = 1 - s1
            t1 = y - j0
            t0 = 1 - t1

            d[j, i] = (
                s0 * (t0 * d0[j0, i0] + t1 * d0[j1, i0]) +
                s1 * (t0 * d0[j0, i1] + t1 * d0[j1, i1])
            )

    set_bnd(b, d)

def project(u, v, p, div):
    """Project velocity field to make it divergence-free"""
    # Calculate divergence
    div[1:-1, 1:-1] = -0.5 * (
        u[1:-1, 2:] - u[1:-1, 0:-2] +
        v[2:, 1:-1] - v[0:-2, 1:-1]
    ) / GRID_SIZE

    p[:] = 0
    set_bnd(0, div)
    set_bnd(0, p)

    # Solve Poisson equation
    for _ in range(ITERATIONS):
        p[1:-1, 1:-1] = (div[1:-1, 1:-1] + (
            p[0:-2, 1:-1] + p[2:, 1:-1] +
            p[1:-1, 0:-2] + p[1:-1, 2:]
        )) / 4

        set_bnd(0, p)

    # Subtract gradient
    u[1:-1, 1:-1] -= 0.5 * (p[1:-1, 2:] - p[1:-1, 0:-2]) * GRID_SIZE
    v[1:-1, 1:-1] -= 0.5 * (p[2:, 1:-1] - p[0:-2, 1:-1]) * GRID_SIZE

    set_bnd(1, u)
    set_bnd(2, v)

def set_bnd(b, x):
    """Set boundary conditions"""
    # Left and right walls
    x[:, 0] = -x[:, 1] if b == 1 else x[:, 1]
    x[:, -1] = -x[:, -2] if b == 1 else x[:, -2]

    # Top and bottom walls
    x[0, :] = -x[1, :] if b == 2 else x[1, :]
    x[-1, :] = -x[-2, :] if b == 2 else x[-2, :]

    # Corners
    x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
    x[0, -1] = 0.5 * (x[1, -1] + x[0, -2])
    x[-1, 0] = 0.5 * (x[-2, 0] + x[-1, 1])
    x[-1, -1] = 0.5 * (x[-2, -1] + x[-1, -2])

def apply_vorticity_confinement():
    """Apply vorticity confinement to enhance swirls"""
    global velocity_x, velocity_y

    # Calculate vorticity
    vorticity = np.zeros_like(velocity_x)
    vorticity[1:-1, 1:-1] = (
        (velocity_y[1:-1, 2:] - velocity_y[1:-1, 0:-2]) -
        (velocity_x[2:, 1:-1] - velocity_x[0:-2, 1:-1])
    ) * 0.5

    # Calculate vorticity gradient
    grad_vort_x = np.zeros_like(vorticity)
    grad_vort_y = np.zeros_like(vorticity)

    grad_vort_x[1:-1, 1:-1] = (
        np.abs(vorticity[1:-1, 2:]) - np.abs(vorticity[1:-1, 0:-2])
    ) * 0.5

    grad_vort_y[1:-1, 1:-1] = (
        np.abs(vorticity[2:, 1:-1]) - np.abs(vorticity[0:-2, 1:-1])
    ) * 0.5

    # Calculate vorticity confinement force
    length = np.sqrt(grad_vort_x**2 + grad_vort_y**2) + 1e-6
    grad_vort_x /= length
    grad_vort_y /= length

    # Apply force
    force_x = grad_vort_y * vorticity * VORTICITY_STRENGTH
    force_y = -grad_vort_x * vorticity * VORTICITY_STRENGTH

    velocity_x += force_x
    velocity_y += force_y

def draw():
    py5.background(*BACKGROUND.astype(int))

    # Create pixel array
    py5.load_np_pixels()
    pixels = py5.np_pixels

    # Get actual canvas size
    canvas_height, canvas_width = pixels.shape[:2]

    # Scale density field to canvas size
    from scipy.ndimage import zoom
    density_scaled = zoom(density, (canvas_height / GRID_SIZE, canvas_width / GRID_SIZE), order=1)

    # Normalize density for color mapping
    density_max = np.max(density_scaled)
    if density_max > 0:
        density_normalized = density_scaled / density_max
    else:
        density_normalized = density_scaled

    # Create color field
    color_field = np.zeros((canvas_height, canvas_width, 3), dtype=np.float64)

    # Mix colors based on density
    for y in range(canvas_height):
        for x in range(canvas_width):
            d = density_normalized[y, x]

            if d > 0.01:
                # Base color is cyan
                base_color = COLOR_CYAN.copy()

                # Add coral based on position (creates variety)
                norm_x = x / canvas_width
                norm_y = y / canvas_height

                if norm_x > 0.5 and norm_y < 0.5:
                    # Upper right quadrant gets coral
                    base_color = base_color * 0.7 + COLOR_CORAL * 0.3
                elif norm_x < 0.3 and norm_y > 0.7:
                    # Lower left quadrant gets amber
                    base_color = base_color * 0.8 + COLOR_AMBER * 0.2

                # Apply density-based brightness
                brightness = min(1.0, d * 2.0)
                final_color = BACKGROUND + (base_color - BACKGROUND) * brightness

                # Add some variation based on local density
                variation = 0.8 + 0.2 * np.sin(x * 0.1) * np.cos(y * 0.1)
                final_color *= variation

                color_field[y, x] = np.clip(final_color, 0, 255)
            else:
                color_field[y, x] = BACKGROUND

    # Apply to pixels
    pixels[:, :, :3] = color_field.astype(int)
    pixels[:, :, 3] = 255  # Alpha

    py5.update_np_pixels()

    # Save preview and exit
    py5.save_frame(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()

py5.run_sketch()
