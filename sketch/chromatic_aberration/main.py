from pathlib import Path
import py5
import numpy as np

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 1

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Optical simulation parameters
NUM_RAYS = 3600
NUM_OPTICAL_ELEMENTS = 15
MAX_BOUNCES = 4
DISPERSION_STRENGTH = 0.25

# Wavelength-dependent refraction indices (simplified RGB model)
# Red (longer wavelength) bends less, violet (shorter) bends more
REFRACTION_RED = 1.50
REFRACTION_GREEN = 1.52
REFRACTION_BLUE = 1.54

# Color palette
BACKGROUND = np.array([26, 26, 26], dtype=np.float64)  # Deep charcoal
WHITE = np.array([255, 255, 255], dtype=np.float64)  # White light source

# Optical elements data
optical_elements = []

def setup():
    py5.size(*SIZE)
    py5.no_loop()

    # Generate optical elements
    generate_optical_elements()

def generate_optical_elements():
    """Generate random optical elements (lenses, prisms)"""
    global optical_elements

    for _ in range(NUM_OPTICAL_ELEMENTS):
        # Random position
        x = np.random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        y = np.random.uniform(SIZE[1] * 0.1, SIZE[1] * 0.9)

        # Random size
        radius = np.random.uniform(50, 150)

        # Random type: 0 = convex lens, 1 = prism, 2 = concave lens
        element_type = np.random.randint(0, 3)

        # Random rotation
        rotation = np.random.uniform(0, 2 * np.pi)

        # Random focal length (for lenses)
        focal_length = np.random.uniform(100, 300)

        optical_elements.append({
            'x': x,
            'y': y,
            'radius': radius,
            'type': element_type,
            'rotation': rotation,
            'focal_length': focal_length
        })

def trace_ray(start_x, start_y, angle, wavelength_factor):
    """Trace a single ray through optical elements with chromatic aberration"""
    x, y = start_x, start_y
    current_angle = angle

    # Wavelength-dependent refraction index
    # wavelength_factor: 0 = red, 0.5 = green, 1 = blue
    refraction_index = REFRACTION_RED + (REFRACTION_BLUE - REFRACTION_RED) * wavelength_factor

    points = [(x, y)]

    dir_x = np.cos(current_angle)
    dir_y = np.sin(current_angle)

    for _ in range(MAX_BOUNCES):
        # Find nearest intersection of current ray with any circular element.
        # Uses ray-circle projection (tangent distance test) to avoid the
        # "must already be inside the circle" bug.
        nearest_t = float('inf')
        nearest_element = None

        for element in optical_elements:
            cx = element['x'] - x
            cy = element['y'] - y
            t_ca = cx * dir_x + cy * dir_y
            if t_ca <= 0:
                continue

            d2 = cx * cx + cy * cy - t_ca * t_ca
            r2 = element['radius'] * element['radius']
            if d2 > r2:
                continue

            t_hc = np.sqrt(max(r2 - d2, 0.0))
            t_hit = t_ca - t_hc
            if t_hit <= 1e-3:
                t_hit = t_ca + t_hc
            if t_hit > 1e-3 and t_hit < nearest_t:
                nearest_t = t_hit
                nearest_element = element

        if nearest_element is None:
            # No intersection, extend ray to edge
            extend_dist = max(SIZE) * 1.2
            points.append((
                x + dir_x * extend_dist,
                y + dir_y * extend_dist
            ))
            break

        # Move to intersection point
        element = nearest_element
        x += dir_x * nearest_t
        y += dir_y * nearest_t
        points.append((x, y))

        # Apply chromatic aberration based on element type
        if element['type'] == 0:  # Convex lens
            # Converging lens - different wavelengths focus at different points
            focal_offset = (refraction_index - 1.5) * element['focal_length'] * DISPERSION_STRENGTH
            angle_to_center = np.arctan2(element['y'] - y, element['x'] - x)
            current_angle = angle_to_center + (current_angle - angle_to_center) * (1 - focal_offset / element['focal_length'])

        elif element['type'] == 1:  # Prism
            # Prism - wavelength-dependent refraction angle
            prism_angle = element['rotation']
            deviation = (refraction_index - 1.5) * DISPERSION_STRENGTH * np.pi / 4
            current_angle += deviation * np.sin(prism_angle - current_angle)

        elif element['type'] == 2:  # Concave lens
            # Diverging lens - different wavelengths diverge at different rates
            focal_offset = (refraction_index - 1.5) * element['focal_length'] * DISPERSION_STRENGTH
            angle_from_center = np.arctan2(y - element['y'], x - element['x'])
            current_angle = angle_from_center + (current_angle - angle_from_center) * (1 + focal_offset / element['focal_length'])

        dir_x = np.cos(current_angle)
        dir_y = np.sin(current_angle)

    return points

def draw():
    py5.background(*BACKGROUND.astype(int))
    py5.no_fill()

    # Subtle vertical gradient background
    py5.stroke_weight(1)
    for y in range(SIZE[1]):
        t = y / max(SIZE[1] - 1, 1)
        c = BACKGROUND + np.array([8, 8, 14]) * t
        py5.stroke(int(c[0]), int(c[1]), int(c[2]), 255)
        py5.line(0, y, SIZE[0], y)

    # Generate light source positions (multiple white light sources)
    light_sources = []
    for _ in range(8):
        x = np.random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        y = np.random.uniform(SIZE[1] * 0.1, SIZE[1] * 0.3)
        light_sources.append((x, y))

    # Draw light source halos first
    py5.no_stroke()
    for light_x, light_y in light_sources:
        for r in [70, 40, 20]:
            a = 8 if r == 70 else (20 if r == 40 else 45)
            py5.fill(255, 255, 255, a)
            py5.circle(light_x, light_y, r * 2)

    # Draw rays with additive blending for visible chromatic separation
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.2)
    for light_x, light_y in light_sources:
        for i in range(NUM_RAYS // len(light_sources)):
            angle = (i / (NUM_RAYS // len(light_sources))) * 2 * np.pi

            # Three wavelength components (RGB) for aberration
            for wavelength_factor, color in [(0.0, [255, 0, 0]), (0.5, [0, 255, 0]), (1.0, [0, 0, 255])]:
                points = trace_ray(light_x, light_y, angle, wavelength_factor)
                for j in range(len(points) - 1):
                    x1, y1 = points[j]
                    x2, y2 = points[j + 1]
                    mx = (x1 + x2) * 0.5
                    my = (y1 + y2) * 0.5
                    dist_from_source = np.sqrt((mx - light_x) ** 2 + (my - light_y) ** 2)
                    alpha = int(np.clip(170 * max(0.12, 1.0 - dist_from_source / 700), 20, 170))
                    py5.stroke(color[0], color[1], color[2], alpha)
                    py5.line(x1, y1, x2, y2)

    py5.blend_mode(py5.BLEND)

    # Draw optical elements (subtle outlines and labels)
    py5.no_fill()
    py5.stroke_weight(1.4)
    for element in optical_elements:
        x, y = element['x'], element['y']
        radius = element['radius']
        if element['type'] == 0:
            py5.stroke(170, 210, 255, 55)  # convex lens
        elif element['type'] == 1:
            py5.stroke(255, 220, 160, 55)  # prism
        else:
            py5.stroke(200, 170, 255, 55)  # concave lens
        py5.circle(x, y, radius * 2)

    # Save preview and exit
    py5.save_frame(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()

py5.run_sketch()
