from pathlib import Path
import py5
import numpy as np

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 1

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Optical simulation parameters
NUM_RAYS = 15000
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

    for bounce in range(MAX_BOUNCES):
        # Find nearest optical element intersection
        nearest_dist = float('inf')
        nearest_element = None
        intersection_point = None

        for element in optical_elements:
            # Check if ray intersects with element
            dx = element['x'] - x
            dy = element['y'] - y
            dist = np.sqrt(dx*dx + dy*dy)

            if dist < element['radius'] and dist < nearest_dist:
                nearest_dist = dist
                nearest_element = element

        if nearest_element is None:
            # No intersection, extend ray to edge
            extend_dist = 1000
            points.append((
                x + np.cos(current_angle) * extend_dist,
                y + np.sin(current_angle) * extend_dist
            ))
            break

        # Calculate intersection point
        element = nearest_element
        dx = element['x'] - x
        dy = element['y'] - y
        dist = np.sqrt(dx*dx + dy*dy)

        # Move to intersection point
        x += np.cos(current_angle) * dist
        y += np.sin(current_angle) * dist
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

    return points

def draw():
    # Create background gradient
    py5.background(*BACKGROUND.astype(int))

    # Create pixel array
    py5.load_np_pixels()
    pixels = py5.np_pixels

    # Get actual canvas size
    canvas_height, canvas_width = pixels.shape[:2]

    # Create background gradient (darker at top, slightly lighter at bottom)
    for y in range(canvas_height):
        gradient_factor = y / canvas_height
        bg_color = BACKGROUND + np.array([10, 10, 15]) * gradient_factor
        pixels[y, :, :3] = np.clip(bg_color, 0, 255).astype(int)
        pixels[y, :, 3] = 255

    # Create accumulation buffer for additive blending
    color_buffer = np.zeros((canvas_height, canvas_width, 3), dtype=np.float64)

    # Generate light source positions (multiple white light sources)
    light_sources = []
    for _ in range(8):
        x = np.random.uniform(canvas_width * 0.1, canvas_width * 0.9)
        y = np.random.uniform(canvas_height * 0.1, canvas_height * 0.3)  # Top area
        light_sources.append((x, y))

    # Trace rays for each light source
    for light_x, light_y in light_sources:
        # Emit rays in all directions
        for i in range(NUM_RAYS // len(light_sources)):
            angle = (i / (NUM_RAYS // len(light_sources))) * 2 * np.pi

            # Trace three wavelength components (RGB) for chromatic aberration
            for wavelength_factor, color in [(0.0, [255, 0, 0]), (0.5, [0, 255, 0]), (1.0, [0, 0, 255])]:
                points = trace_ray(light_x, light_y, angle, wavelength_factor)

                # Draw ray segments with additive blending
                for j in range(len(points) - 1):
                    x1, y1 = points[j]
                    x2, y2 = points[j + 1]

                    # Clip to canvas bounds
                    x1 = max(0, min(canvas_width - 1, x1))
                    y1 = max(0, min(canvas_height - 1, y1))
                    x2 = max(0, min(canvas_width - 1, x2))
                    y2 = max(0, min(canvas_height - 1, y2))

                    # Draw line segment
                    length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    if length > 0:
                        steps = int(length) + 1
                        for t in range(steps):
                            t_norm = t / steps
                            px = int(x1 + (x2 - x1) * t_norm)
                            py = int(y1 + (y2 - y1) * t_norm)

                            if 0 <= px < canvas_width and 0 <= py < canvas_height:
                                # Intensity based on distance from light source
                                dist_from_source = np.sqrt((px - light_x)**2 + (py - light_y)**2)
                                intensity = max(0, 1 - dist_from_source / 600)

                                # Enhanced color saturation and brightness
                                color_enhanced = np.array(color) * 1.5  # Boost saturation
                                color_enhanced = np.clip(color_enhanced, 0, 255)

                                # Add color with additive blending (increased intensity)
                                color_buffer[py, px] += color_enhanced * intensity * 0.8

    # Draw optical elements (subtle outlines)
    for element in optical_elements:
        x, y = int(element['x']), int(element['y'])
        radius = int(element['radius'])

        # Draw subtle outline
        for angle in np.linspace(0, 2 * np.pi, 100):
            px = int(x + radius * np.cos(angle))
            py = int(y + radius * np.sin(angle))

            if 0 <= px < canvas_width and 0 <= py < canvas_height:
                color_buffer[py, px] += np.array([80, 80, 80]) * 0.3

    # Add glow effects around light sources
    for light_x, light_y in light_sources:
        lx, ly = int(light_x), int(light_y)
        glow_radius = 80

        for dy in range(-glow_radius, glow_radius + 1):
            for dx in range(-glow_radius, glow_radius + 1):
                px = lx + dx
                py = ly + dy

                if 0 <= px < canvas_width and 0 <= py < canvas_height:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < glow_radius:
                        # White glow with falloff
                        glow_intensity = (1 - dist / glow_radius) ** 2
                        color_buffer[py, px] += np.array([255, 255, 255]) * glow_intensity * 0.5

    # Normalize and apply to pixels
    color_max = np.max(color_buffer)
    if color_max > 0:
        color_buffer = np.clip(color_buffer / color_max * 255, 0, 255)

    # Apply to pixels with additive blending
    for y in range(canvas_height):
        for x in range(canvas_width):
            # Blend background with color buffer
            bg_intensity = 0.3  # Background visibility
            color_intensity = 0.7  # Color buffer visibility

            final_color = (
                pixels[y, x, :3] * bg_intensity +
                color_buffer[y, x] * color_intensity
            )

            pixels[y, x, :3] = np.clip(final_color, 0, 255).astype(int)
            pixels[y, x, 3] = 255  # Alpha

    py5.update_np_pixels()

    # Save preview and exit
    py5.save_frame(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()

py5.run_sketch()
