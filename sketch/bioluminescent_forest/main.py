import py5
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import exit_after_preview_py5
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
NUM_TREES = 15
NUM_PARTICLES = 2000
MAX_TREE_DEPTH = 6
MIN_BRANCH_SIZE = 3
INTERACTION_RADIUS = 60
GLOW_FREQ_MIN = 0.5
GLOW_FREQ_MAX = 2.0

# Colors
BACKGROUND = py5.color(8, 12, 20)  # Deep forest dark
COLOR_TEAL = np.array([0, 255, 204])  # Electric teal
COLOR_AMBER = np.array([255, 204, 0])  # Warm amber
COLOR_VIOLET = np.array([170, 136, 255])  # Soft violet
COLOR_PURPLE = np.array([180, 100, 255])  # Deep purple
COLOR_MAGENTA = np.array([255, 100, 200])  # Magenta accent

# Tree data
trees = []
particles = None
particle_velocities = None
particle_phases = None
particle_frequencies = None
particle_depths = None
particle_colors = None
particle_glow_strength = None

class Tree:
    def __init__(self, x, y, base_size, depth, angle, age_factor):
        self.x = x
        self.y = y
        self.base_size = base_size
        self.depth = depth
        self.angle = angle
        self.age_factor = age_factor  # 0-1, affects color and glow
        self.branches = []

    def generate_branches(self):
        if self.depth <= 0 or self.base_size < MIN_BRANCH_SIZE:
            return

        # Randomized branch parameters
        num_branches = np.random.randint(2, 4)
        angle_spread = np.random.uniform(0.3, 0.8)

        for i in range(num_branches):
            # Calculate branch angle
            branch_angle = self.angle + (i - num_branches/2) * angle_spread
            branch_angle += np.random.uniform(-0.1, 0.1)

            # Calculate branch size with variation
            size_factor = np.random.uniform(0.6, 0.85)
            branch_size = self.base_size * size_factor

            # Calculate branch end position
            end_x = self.x + np.cos(branch_angle) * branch_size
            end_y = self.y + np.sin(branch_angle) * branch_size

            # Create branch
            branch = Tree(end_x, end_y, branch_size, self.depth - 1,
                         branch_angle, self.age_factor)
            self.branches.append(branch)
            branch.generate_branches()

    def draw(self, surface):
        # Calculate color based on age and depth
        depth_factor = 1 - (self.depth / MAX_TREE_DEPTH)

        # Base color varies with age
        if self.age_factor < 0.3:
            base_color = COLOR_TEAL
        elif self.age_factor < 0.6:
            base_color = COLOR_AMBER
        else:
            base_color = COLOR_VIOLET

        # Add purple/magenta accents in deeper areas
        if self.depth > 3 and np.random.random() < 0.3:
            if np.random.random() < 0.5:
                base_color = COLOR_PURPLE
            else:
                base_color = COLOR_MAGENTA

        # Brightness based on depth and age
        brightness = 80 + 100 * depth_factor * (0.5 + 0.5 * self.age_factor)

        # Size based on depth (closer = larger)
        size = max(1, self.base_size * (0.5 + 0.5 * depth_factor))

        # Draw branch with glow
        surface.fill(base_color[0], base_color[1], base_color[2], brightness)
        surface.circle(self.x, self.y, size)

        # Draw glow halo for larger branches
        if size > 2:
            halo_size = size * 2
            halo_brightness = brightness * 0.25
            surface.fill(base_color[0], base_color[1], base_color[2], halo_brightness)
            surface.circle(self.x, self.y, halo_size)

        # Recursively draw branches
        for branch in self.branches:
            branch.draw(surface)

def setup():
    global trees, particles, particle_velocities, particle_phases
    global particle_frequencies, particle_depths, particle_colors, particle_glow_strength

    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_loop()
    py5.no_stroke()

    # Generate trees with randomized parameters
    for _ in range(NUM_TREES):
        x = np.random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        y = np.random.uniform(SIZE[1] * 0.3, SIZE[1] * 0.9)
        base_size = np.random.uniform(40, 80)
        depth = np.random.randint(4, MAX_TREE_DEPTH + 1)
        angle = -np.pi / 2 + np.random.uniform(-0.2, 0.2)  # Generally upward
        age_factor = np.random.uniform(0, 1)

        tree = Tree(x, y, base_size, depth, angle, age_factor)
        tree.generate_branches()
        trees.append(tree)

    # Initialize particles
    particles = np.random.rand(NUM_PARTICLES, 2) * SIZE
    particle_velocities = (np.random.rand(NUM_PARTICLES, 2) - 0.5) * 2
    particle_phases = np.random.rand(NUM_PARTICLES) * 2 * np.pi
    particle_frequencies = GLOW_FREQ_MIN + np.random.rand(NUM_PARTICLES) * (GLOW_FREQ_MAX - GLOW_FREQ_MIN)
    particle_depths = np.random.rand(NUM_PARTICLES)

    # Pre-calculate colors with more variety
    particle_colors = np.zeros((NUM_PARTICLES, 3))
    for i in range(NUM_PARTICLES):
        # Mix colors based on position and depth
        norm_x = particles[i, 0] / SIZE[0]
        norm_y = particles[i, 1] / SIZE[1]
        depth = particle_depths[i]

        # Base gradient
        if norm_x < 0.33:
            base = COLOR_TEAL
        elif norm_x < 0.66:
            base = COLOR_AMBER
        else:
            base = COLOR_VIOLET

        # Add purple/magenta accents in deeper areas
        if depth > 0.7 and np.random.random() < 0.4:
            if np.random.random() < 0.5:
                base = COLOR_PURPLE
            else:
                base = COLOR_MAGENTA

        particle_colors[i] = base

    # Calculate glow strength based on position (near trees = stronger)
    particle_glow_strength = np.ones(NUM_PARTICLES)
    for i in range(NUM_PARTICLES):
        pos = particles[i]
        min_dist = float('inf')
        for tree in trees:
            dist = np.linalg.norm(pos - np.array([tree.x, tree.y]))
            if dist < min_dist:
                min_dist = dist

        # Stronger glow near trees
        if min_dist < 150:
            particle_glow_strength[i] = 1.0 + 0.5 * (1 - min_dist / 150)

def update_particles():
    global particles, particle_velocities, particle_phases

    # Calculate attraction points (tree canopies and forest floor)
    attraction_points = []
    for tree in trees:
        # Tree canopy (top of tree)
        canopy_y = tree.y - tree.base_size * 2
        attraction_points.append(np.array([tree.x, canopy_y]))

    # Forest floor (bottom area)
    floor_points = 5
    for _ in range(floor_points):
        fx = np.random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        fy = np.random.uniform(SIZE[1] * 0.8, SIZE[1] * 0.95)
        attraction_points.append(np.array([fx, fy]))

    # Update each particle
    for i in range(NUM_PARTICLES):
        pos = particles[i]
        vel = particle_velocities[i]

        # Attraction to nearest attraction point
        nearest_point = attraction_points[np.random.randint(len(attraction_points))]
        to_point = nearest_point - pos
        dist = np.linalg.norm(to_point)

        if dist > 0:
            attraction = to_point / dist * 0.02
            vel += attraction

        # Random wandering
        wander = (np.random.rand(2) - 0.5) * 0.3
        vel += wander

        # Vertical drift (thermal currents)
        vel[1] -= 0.05

        # Limit speed
        speed = np.linalg.norm(vel)
        if speed > 1.5:
            vel = vel / speed * 1.5

        particle_velocities[i] = vel

    # Update positions
    particles += particle_velocities

    # Wrap around edges
    particles[:, 0] = particles[:, 0] % SIZE[0]
    particles[:, 1] = particles[:, 1] % SIZE[1]

    # Update phases
    particle_phases += particle_frequencies * 0.1

def draw_ground_vegetation():
    # Draw ground vegetation, moss patches, and fallen branches
    for _ in range(30):
        x = np.random.uniform(SIZE[0] * 0.05, SIZE[0] * 0.95)
        y = np.random.uniform(SIZE[1] * 0.85, SIZE[1] * 0.98)

        # Small recursive structures for vegetation
        size = np.random.uniform(2, 6)
        depth = np.random.randint(2, 4)

        # Color varies
        if np.random.random() < 0.5:
            color = COLOR_PURPLE
        else:
            color = COLOR_MAGENTA

        brightness = np.random.uniform(40, 80)
        py5.fill(color[0], color[1], color[2], brightness)
        py5.circle(x, y, size)

        # Add glow
        halo_size = size * 2
        halo_brightness = brightness * 0.2
        py5.fill(color[0], color[1], color[2], halo_brightness)
        py5.circle(x, y, halo_size)

def draw():
    py5.background(BACKGROUND)

    # Draw ground vegetation first (background layer)
    draw_ground_vegetation()

    # Update particles
    update_particles()

    # Calculate glow
    glow = 0.5 + 0.5 * np.sin(particle_phases)
    glow_amplified = glow * particle_glow_strength

    # Render trees with depth compositing
    # Sort trees by y position for proper layering
    trees_sorted = sorted(trees, key=lambda t: t.y)

    for tree in trees_sorted:
        tree.draw(py5)

    # Render particles with depth compositing
    depth_order = np.argsort(particle_depths)

    for idx in depth_order:
        x, y = particles[idx]
        z = particle_depths[idx]
        g = glow_amplified[idx]
        color = particle_colors[idx]

        # Size based on depth (closer = larger)
        base_size = 2 + z * 3
        size = base_size * (0.7 + 0.5 * g)

        # Brightness based on depth and glow
        brightness = 120 + 100 * g * (0.6 + 0.4 * z)

        # Opacity based on depth (closer = more opaque)
        alpha = int(150 + 105 * z)

        # Draw particle with additive blending
        py5.fill(color[0], color[1], color[2], alpha)
        py5.circle(x, y, size)

        # Draw glow halo
        halo_size = size * 2
        halo_brightness = brightness * 0.25
        py5.fill(color[0], color[1], color[2], halo_brightness)
        py5.circle(x, y, halo_size)

    # Save preview and exit
    exit_after_preview_py5(SKETCH_DIR, filename="preview.png")

py5.run_sketch()
