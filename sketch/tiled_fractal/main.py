from pathlib import Path
import py5
import numpy as np

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 1

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

MAX_DEPTH = 6  # Recursion depth
MIN_SIZE = 4   # Minimum square size

# Color palette - more dramatic transitions
BACKGROUND = np.array([26, 26, 26], dtype=np.float64)  # Deep charcoal
# Gradient from deep emerald to bright teal
DEEP_EMERALD = np.array([16, 100, 80], dtype=np.float64)
BRIGHT_TEAL = np.array([0, 200, 200], dtype=np.float64)
# Gradient from amber to coral
DEEP_AMBER = np.array([180, 100, 20], dtype=np.float64)
BRIGHT_CORAL = np.array([255, 120, 80], dtype=np.float64)
# Accent colors
GOLD = np.array([255, 215, 0], dtype=np.float64)
VIOLET = np.array([180, 100, 255], dtype=np.float64)

def setup():
    py5.size(*SIZE)
    py5.background(*BACKGROUND.astype(int))
    py5.no_stroke()

    # Create pixel array for direct manipulation
    py5.load_np_pixels()
    pixels = py5.np_pixels

    # Start recursive subdivision from the center
    center_x = SIZE[0] // 2
    center_y = SIZE[1] // 2
    initial_size = min(SIZE[0], SIZE[1]) // 2

    # Use a seed for reproducible organic variation
    seed = 42

    # Draw the fractal pattern with initial rotation
    draw_recursive_square(pixels, center_x, center_y, initial_size, 0, 0, seed)

    py5.update_np_pixels()

def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()

def draw_recursive_square(pixels, x, y, size, depth, rotation, seed):
    """Recursively draw subdivided squares with organic asymmetry and rotation"""
    if size < MIN_SIZE or depth >= MAX_DEPTH:
        return

    # Calculate color based on depth with dramatic transitions
    progress = depth / MAX_DEPTH

    # Use gradient transitions between colors
    if depth % 2 == 0:
        # Emerald to teal gradient
        t = progress
        base_color = DEEP_EMERALD * (1 - t) + BRIGHT_TEAL * t
    else:
        # Amber to coral gradient
        t = progress
        base_color = DEEP_AMBER * (1 - t) + BRIGHT_CORAL * t

    # Add accent colors at specific depths for visual interest
    if depth == 2:
        base_color = base_color * 0.7 + GOLD * 0.3
    elif depth == 4:
        base_color = base_color * 0.8 + VIOLET * 0.2

    # Vary color intensity based on position and depth
    x_norm = x / SIZE[0]
    y_norm = y / SIZE[1]
    intensity = 0.4 + 0.6 * np.sin(x_norm * np.pi * 2 + y_norm * np.pi * 2 + depth * 0.5)

    color = base_color * intensity

    # Draw the current square with rotation
    half_size = size // 2

    # Create rotation matrix
    angle = rotation * np.pi / 8  # 22.5 degree increments
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)

    # Draw rotated square
    for py in range(max(0, y - half_size), min(SIZE[1], y + half_size)):
        for px in range(max(0, x - half_size), min(SIZE[0], x + half_size)):
            # Rotate coordinates
            dx = px - x
            dy = py - y
            rotated_x = dx * cos_a - dy * sin_a
            rotated_y = dx * sin_a + dy * cos_a

            # Check if point is inside rotated square
            if abs(rotated_x) < half_size and abs(rotated_y) < half_size:
                # Add organic variation based on position
                local_x = rotated_x / half_size
                local_y = rotated_y / half_size
                variation = 0.7 + 0.3 * np.sin(local_x * np.pi * 1.5) * np.sin(local_y * np.pi * 1.5)

                # Add depth-based variation
                depth_variation = 1.0 - 0.2 * progress

                final_color = np.clip(color * variation * depth_variation, 0, 255).astype(int)
                pixels[py, px] = [final_color[0], final_color[1], final_color[2], 255]

    # Asymmetric subdivision - different sizes for each quadrant
    # Use seed for organic variation
    np.random.seed(seed + depth)

    # Create asymmetric sizes for 4 quadrants
    base_new_size = size // 3
    size_variations = [
        base_new_size + np.random.randint(-2, 3),  # Top-left
        base_new_size + np.random.randint(-2, 3),  # Top-right
        base_new_size + np.random.randint(-2, 3),  # Bottom-left
        base_new_size + np.random.randint(-2, 3),  # Bottom-right
    ]

    # Calculate asymmetric offsets
    offsets = [
        size // 3 + np.random.randint(-1, 2),  # Top-left
        size // 3 + np.random.randint(-1, 2),  # Top-right
        size // 3 + np.random.randint(-1, 2),  # Bottom-left
        size // 3 + np.random.randint(-1, 2),  # Bottom-right
    ]

    # Recursively subdivide with different rotations for each quadrant
    rotations = [rotation + 1, rotation - 1, rotation + 2, rotation - 2]

    # Top-left
    draw_recursive_square(pixels, x - offsets[0], y - offsets[0],
                         size_variations[0], depth + 1, rotations[0], seed + 1)
    # Top-right
    draw_recursive_square(pixels, x + offsets[1], y - offsets[1],
                         size_variations[1], depth + 1, rotations[1], seed + 2)
    # Bottom-left
    draw_recursive_square(pixels, x - offsets[2], y + offsets[2],
                         size_variations[2], depth + 1, rotations[2], seed + 3)
    # Bottom-right
    draw_recursive_square(pixels, x + offsets[3], y + offsets[3],
                         size_variations[3], depth + 1, rotations[3], seed + 4)

py5.run_sketch()