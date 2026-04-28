from pathlib import Path
import py5
import numpy as np

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 1

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Cellular automaton parameters
GRID_SIZE = 200  # Simulation grid size (higher = more detailed)
NUM_GENERATIONS = 180  # Number of generations to simulate
NUM_SEEDS = 12  # Number of random seed clusters
SEED_RADIUS = 10  # Radius of seed clusters
DENSITY_THRESHOLD = 0.5  # Density threshold for golden amber highlights

# Color palette - more adventurous
BACKGROUND = np.array([8, 15, 25], dtype=np.float64)  # Deep midnight
COLOR_MAGENTA = np.array([255, 0, 128], dtype=np.float64)  # Electric magenta
COLOR_TEAL = np.array([0, 200, 180], dtype=np.float64)  # Bright teal
COLOR_GOLD = np.array([255, 215, 0], dtype=np.float64)  # Rich gold
COLOR_PURPLE = np.array([180, 0, 255], dtype=np.float64)  # Deep purple

# Cellular automaton grid
grid = None
age_grid = None

def setup():
    global grid, age_grid

    py5.size(*SIZE)
    py5.no_loop()

    # Initialize grid
    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
    age_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)

    # Add random seeds
    add_seeds()

    # Simulate for several generations
    for generation in range(NUM_GENERATIONS):
        step()

def add_seeds():
    """Add random seed clusters to the grid"""
    global grid

    for _ in range(NUM_SEEDS):
        # Random position
        x = np.random.randint(10, GRID_SIZE - 10)
        y = np.random.randint(10, GRID_SIZE - 10)

        # Add random cluster
        for dy in range(-SEED_RADIUS, SEED_RADIUS + 1):
            for dx in range(-SEED_RADIUS, SEED_RADIUS + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < SEED_RADIUS:
                        # Random probability based on distance from center
                        prob = 0.8 * (1 - dist/SEED_RADIUS)
                        if np.random.random() < prob:
                            grid[ny, nx] = 1
                            age_grid[ny, nx] = 0

def count_neighbors(grid, x, y):
    """Count the number of live neighbors for a cell"""
    count = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                count += grid[ny, nx]
    return count

def step():
    """Perform one generation of probabilistic cellular automaton"""
    global grid, age_grid

    new_grid = np.zeros_like(grid)
    new_age_grid = np.zeros_like(age_grid)

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            neighbors = count_neighbors(grid, x, y)

            if grid[y, x] == 1:  # Live cell
                # Probabilistic survival: more neighbors = higher survival chance
                survival_prob = 0.3 + 0.7 * (neighbors / 8.0)
                if np.random.random() < survival_prob:
                    new_grid[y, x] = 1
                    new_age_grid[y, x] = age_grid[y, x] + 1
                else:
                    new_grid[y, x] = 0
                    new_age_grid[y, x] = 0
            else:  # Dead cell
                # Probabilistic birth: more neighbors = higher birth chance
                birth_prob = 0.1 * (neighbors / 8.0)
                if np.random.random() < birth_prob:
                    new_grid[y, x] = 1
                    new_age_grid[y, x] = 0
                else:
                    new_grid[y, x] = 0
                    new_age_grid[y, x] = 0

    grid = new_grid
    age_grid = new_age_grid

def draw():
    # Create background
    py5.background(*BACKGROUND.astype(int))

    # Create pixel array
    py5.load_np_pixels()
    pixels = py5.np_pixels

    # Get actual canvas size
    canvas_height, canvas_width = pixels.shape[:2]

    # Scale grid to canvas size
    from scipy.ndimage import zoom
    grid_scaled = zoom(grid, (canvas_height / GRID_SIZE, canvas_width / GRID_SIZE), order=0)
    age_scaled = zoom(age_grid, (canvas_height / GRID_SIZE, canvas_width / GRID_SIZE), order=0)

    # Calculate local density for golden amber highlights
    from scipy.ndimage import uniform_filter
    density = uniform_filter(grid_scaled.astype(np.float64), size=12)

    # Normalize age for color mapping
    age_max = np.max(age_scaled)
    if age_max > 0:
        age_normalized = age_scaled / age_max
    else:
        age_normalized = age_scaled

    # Normalize density for golden amber highlights
    density_max = np.max(density)
    if density_max > 0:
        density_normalized = density / density_max
    else:
        density_normalized = density

    # Create color field
    color_field = np.zeros((canvas_height, canvas_width, 3), dtype=np.float64)

    # Mix colors based on cell state, age, and density
    for y in range(canvas_height):
        for x in range(canvas_width):
            cell_state = grid_scaled[y, x]
            cell_age = age_normalized[y, x]
            local_density = density_normalized[y, x]

            if cell_state > 0.5:  # Live cell
                # Base color is magenta
                base_color = COLOR_MAGENTA.copy()

                # Add teal based on age (older cells get more teal)
                base_color = base_color * (1 - cell_age * 0.6) + COLOR_TEAL * (cell_age * 0.6)

                # Add gold for high-density clusters (more pronounced)
                if local_density > DENSITY_THRESHOLD:
                    density_factor = (local_density - DENSITY_THRESHOLD) / (1 - DENSITY_THRESHOLD)
                    base_color = base_color * (1 - density_factor * 0.7) + COLOR_GOLD * (density_factor * 0.7)

                # Add purple for very old cells
                if cell_age > 0.8:
                    base_color = base_color * 0.7 + COLOR_PURPLE * 0.3

                # Add some variation based on position
                norm_x = x / canvas_width
                norm_y = y / canvas_height

                if norm_x > 0.6 and norm_y < 0.4:
                    # Upper right quadrant gets more gold
                    base_color = base_color * 0.7 + COLOR_GOLD * 0.3
                elif norm_x < 0.4 and norm_y > 0.6:
                    # Lower left quadrant gets more purple
                    base_color = base_color * 0.8 + COLOR_PURPLE * 0.2

                # Add some variation based on local age
                variation = 0.85 + 0.15 * np.sin(x * 0.08) * np.cos(y * 0.08)
                base_color *= variation

                color_field[y, x] = np.clip(base_color, 0, 255)
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
