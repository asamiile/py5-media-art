from pathlib import Path
import py5
import numpy as np
from scipy.fft import fft2, fftshift

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 1

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Diffraction simulation parameters
GRID_SIZE = 512  # Simulation grid size (higher = more detailed)
NUM_APERTURES = 12  # Number of apertures
DIFFRACTION_SCALE = 0.5  # Scale of diffraction pattern
INTENSITY_SCALE = 2.0  # Intensity scaling factor

# Color palette
BACKGROUND = np.array([10, 10, 26], dtype=np.float64)  # Deep midnight navy
COLOR_CYAN = np.array([0, 212, 255], dtype=np.float64)  # Electric cyan
COLOR_CORAL = np.array([255, 107, 107], dtype=np.float64)  # Warm coral
COLOR_AMBER = np.array([255, 217, 61], dtype=np.float64)  # Golden amber

# Aperture data
apertures = []

def setup():
    py5.size(*SIZE)
    py5.no_loop()

    # Generate apertures
    generate_apertures()

def generate_apertures():
    """Generate random apertures (circular, rectangular, double slit)"""
    global apertures

    for _ in range(NUM_APERTURES):
        # Random position
        x = np.random.uniform(GRID_SIZE * 0.2, GRID_SIZE * 0.8)
        y = np.random.uniform(GRID_SIZE * 0.2, GRID_SIZE * 0.8)

        # Random size
        size = np.random.uniform(20, 60)

        # Random type: 0 = circular, 1 = rectangular, 2 = double slit
        aperture_type = np.random.randint(0, 3)

        # Random rotation (for rectangular)
        rotation = np.random.uniform(0, np.pi)

        # Random slit separation (for double slit)
        slit_separation = np.random.uniform(30, 80)

        apertures.append({
            'x': x,
            'y': y,
            'size': size,
            'type': aperture_type,
            'rotation': rotation,
            'slit_separation': slit_separation
        })

def create_aperture_field():
    """Create the aperture field (transmission function)"""
    aperture_field = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.complex128)

    # Create coordinate grid
    y_coords, x_coords = np.mgrid[0:GRID_SIZE, 0:GRID_SIZE]

    for aperture in apertures:
        # Calculate distance from aperture center
        dx = x_coords - aperture['x']
        dy = y_coords - aperture['y']

        if aperture['type'] == 0:  # Circular aperture
            # Circular aperture: transmission = 1 inside circle, 0 outside
            radius = aperture['size'] / 2
            dist = np.sqrt(dx**2 + dy**2)
            mask = dist <= radius
            aperture_field[mask] += 1.0

        elif aperture['type'] == 1:  # Rectangular aperture
            # Rectangular aperture with rotation
            width = aperture['size']
            height = aperture['size'] * 0.6

            # Rotate coordinates
            cos_rot = np.cos(aperture['rotation'])
            sin_rot = np.sin(aperture['rotation'])

            dx_rot = dx * cos_rot + dy * sin_rot
            dy_rot = -dx * sin_rot + dy * cos_rot

            mask = (np.abs(dx_rot) <= width/2) & (np.abs(dy_rot) <= height/2)
            aperture_field[mask] += 1.0

        elif aperture['type'] == 2:  # Double slit
            # Two parallel slits
            slit_width = aperture['size'] * 0.3
            separation = aperture['slit_separation']

            # Slit 1
            mask1 = (np.abs(dx) <= slit_width/2) & (np.abs(dy - separation/2) <= aperture['size'])
            aperture_field[mask1] += 1.0

            # Slit 2
            mask2 = (np.abs(dx) <= slit_width/2) & (np.abs(dy + separation/2) <= aperture['size'])
            aperture_field[mask2] += 1.0

    return aperture_field

def compute_diffraction_pattern(aperture_field):
    """Compute diffraction pattern using Fourier transform"""
    # Compute 2D FFT
    fft_result = fft2(aperture_field)

    # Shift zero frequency to center
    fft_shifted = fftshift(fft_result)

    # Compute intensity (magnitude squared)
    intensity = np.abs(fft_shifted)**2

    # Normalize intensity
    intensity_max = np.max(intensity)
    if intensity_max > 0:
        intensity = intensity / intensity_max

    return intensity

def draw():
    # Create background
    py5.background(*BACKGROUND.astype(int))

    # Create pixel array
    py5.load_np_pixels()
    pixels = py5.np_pixels

    # Get actual canvas size
    canvas_height, canvas_width = pixels.shape[:2]

    # Create aperture field
    aperture_field = create_aperture_field()

    # Compute diffraction pattern
    diffraction_pattern = compute_diffraction_pattern(aperture_field)

    # Scale diffraction pattern to canvas size
    from scipy.ndimage import zoom
    diffraction_scaled = zoom(diffraction_pattern,
                              (canvas_height / GRID_SIZE, canvas_width / GRID_SIZE),
                              order=1)

    # Normalize diffraction pattern
    diffraction_max = np.max(diffraction_scaled)
    if diffraction_max > 0:
        diffraction_normalized = diffraction_scaled / diffraction_max
    else:
        diffraction_normalized = diffraction_scaled

    # Create color field
    color_field = np.zeros((canvas_height, canvas_width, 3), dtype=np.float64)

    # Mix colors based on diffraction intensity
    for y in range(canvas_height):
        for x in range(canvas_width):
            intensity = diffraction_normalized[y, x]

            if intensity > 0.01:
                # Base color is cyan
                base_color = COLOR_CYAN.copy()

                # Add coral based on position (creates variety)
                norm_x = x / canvas_width
                norm_y = y / canvas_height

                # Create radial variation
                center_x, center_y = canvas_width / 2, canvas_height / 2
                dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                max_dist = np.sqrt(center_x**2 + center_y**2)
                radial_factor = dist_from_center / max_dist

                if norm_x > 0.5 and norm_y < 0.5:
                    # Upper right quadrant gets coral
                    base_color = base_color * 0.7 + COLOR_CORAL * 0.3
                elif norm_x < 0.3 and norm_y > 0.7:
                    # Lower left quadrant gets amber
                    base_color = base_color * 0.8 + COLOR_AMBER * 0.2

                # Apply intensity-based brightness with power law for contrast
                brightness = min(1.0, intensity ** 0.5 * INTENSITY_SCALE)
                final_color = BACKGROUND + (base_color - BACKGROUND) * brightness

                # Add some variation based on local intensity
                variation = 0.9 + 0.1 * np.sin(x * 0.05) * np.cos(y * 0.05)
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
