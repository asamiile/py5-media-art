"""
tidal_erosion — The ancient dialogue between ocean and stone
A cross-section coastal cliff revealing layered geological strata,
undercut by simulated wave erosion over millennia. The cliff is rendered
using vectorized numpy operations with multi-octave noise for natural
erosion patterns. Seafoam traces the active waterline.
"""

from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import gaussian_filter
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 120

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Color palette ---
OCEAN_DEEP = np.array([8, 18, 32], dtype=np.float64)
OCEAN_SURFACE = np.array([22, 52, 78], dtype=np.float64)
SEAFOAM = np.array([128, 195, 185], dtype=np.float64)
FOAM_WHITE = np.array([230, 238, 235], dtype=np.float64)
SKY_TOP = np.array([10, 15, 28], dtype=np.float64)
SKY_HORIZON = np.array([28, 38, 58], dtype=np.float64)

# Strata colors (bottom→top = ancient→young)
STRATA_COLORS = [
    np.array([42, 38, 35], dtype=np.float64),     # deep basalt
    np.array([62, 58, 52], dtype=np.float64),      # dark slate
    np.array([78, 82, 95], dtype=np.float64),      # blue-grey rock
    np.array([95, 88, 72], dtype=np.float64),      # mudstone
    np.array([118, 105, 82], dtype=np.float64),    # sandstone
    np.array([158, 135, 95], dtype=np.float64),    # ochre sediment
    np.array([138, 128, 108], dtype=np.float64),   # limestone
    np.array([108, 115, 98], dtype=np.float64),    # green shale
    np.array([145, 138, 125], dtype=np.float64),   # pale clay
    np.array([85, 75, 62], dtype=np.float64),      # iron oxide
    np.array([125, 118, 105], dtype=np.float64),   # dolomite
    np.array([155, 145, 128], dtype=np.float64),   # top soil
]

WATERLINE_FRAC = 0.60  # waterline at 60% of height


def noise_2d(h, w, octaves=5, persistence=0.5, scale=0.005):
    """Generate 2D fractal noise using Fourier method."""
    # Create noise in frequency domain
    noise = np.zeros((h, w), dtype=np.float64)
    amp = 1.0
    for i in range(octaves):
        freq = scale * (2 ** i)
        # Generate smooth noise at this frequency
        n = np.random.randn(h, w)
        sigma = max(1, 1.0 / (freq * 20))
        smoothed = gaussian_filter(n, sigma=sigma)
        noise += smoothed * amp
        amp *= persistence
    # Normalize
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-10)
    return noise


def build_cliff_and_erode():
    """Build cliff terrain and apply erosion, returning terrain mask."""
    w, h = SIZE
    waterline_y = int(h * WATERLINE_FRAC)
    
    terrain = np.zeros((h, w), dtype=bool)
    
    # Cliff occupies the right ~60% of canvas
    # Generate cliff face profile (left boundary of rock)
    cliff_face = np.zeros(h, dtype=np.float64)
    
    # Multi-frequency cliff face profile
    face_noise = np.zeros(h, dtype=np.float64)
    for freq, amp in [(0.003, 80), (0.007, 40), (0.015, 20), (0.03, 10)]:
        phase = np.random.uniform(0, 2 * np.pi)
        face_noise += np.sin(np.arange(h) * freq * 2 * np.pi + phase) * amp
    
    # Cliff shape: wider at top, undercut at waterline, solid at base
    for y in range(h):
        t = y / h
        if t < 0.25:
            # Sky — no rock
            cliff_face[y] = w
        elif t < 0.35:
            # Cliff top emerging
            emerge_t = (t - 0.25) / 0.10
            cliff_face[y] = w * (0.85 - 0.40 * emerge_t ** 0.5) + face_noise[y] * 0.5
        elif t < WATERLINE_FRAC:
            # Main cliff face — sweeps leftward
            face_t = (t - 0.35) / (WATERLINE_FRAC - 0.35)
            cliff_face[y] = w * (0.45 - 0.12 * face_t) + face_noise[y]
        elif t < 0.75:
            # Undercut zone — pushes rightward (erosion notch)
            undercut_t = (t - WATERLINE_FRAC) / 0.15
            notch_depth = 60 + np.sin(undercut_t * np.pi) * 100
            cliff_face[y] = w * 0.33 + notch_depth + face_noise[y]
        else:
            # Base — solid, extends left
            cliff_face[y] = w * 0.28 + face_noise[y] * 0.7
    
    # Smooth the face
    cliff_face = gaussian_filter(cliff_face, sigma=5)
    
    # Fill terrain grid
    yy, xx = np.mgrid[0:h, 0:w]
    terrain = xx >= cliff_face[yy].astype(int)
    
    # Apply detailed erosion using 2D noise
    erosion_noise = noise_2d(h, w, octaves=6, persistence=0.55, scale=0.008)
    
    # Erosion is strongest near waterline
    erosion_strength = np.zeros((h, w), dtype=np.float64)
    for y in range(h):
        dy = abs(y - waterline_y)
        erosion_strength[y, :] = np.exp(-dy ** 2 / (80 ** 2)) * 1.0
    
    # Apply erosion: remove rock where noise * strength > threshold
    erosion_mask = (erosion_noise * erosion_strength) > 0.35
    terrain &= ~erosion_mask
    
    # Add sea caves: larger random cavities near waterline
    n_caves = np.random.randint(3, 7)
    for _ in range(n_caves):
        cave_cy = waterline_y + np.random.randint(-50, 30)
        # Find rock edge at this height
        rock_at_y = np.where(terrain[np.clip(cave_cy, 0, h-1), :])[0]
        if len(rock_at_y) == 0:
            continue
        cave_cx = rock_at_y[0] + np.random.randint(10, 80)
        cave_rx = np.random.randint(25, 80)
        cave_ry = np.random.randint(10, 40)
        
        # Elliptical cave with noise boundary
        cave_dist = ((xx - cave_cx) / cave_rx) ** 2 + ((yy - cave_cy) / cave_ry) ** 2
        cave_noise = noise_2d(h, w, octaves=3, persistence=0.5, scale=0.02)
        cave_mask = cave_dist < (0.8 + cave_noise * 0.4)
        terrain &= ~cave_mask
    
    # Add vertical cracks in cliff face
    n_cracks = np.random.randint(5, 15)
    for _ in range(n_cracks):
        crack_x = np.random.randint(int(w * 0.3), int(w * 0.9))
        crack_y_start = np.random.randint(int(h * 0.25), int(h * 0.55))
        crack_length = np.random.randint(30, 150)
        crack_width = np.random.randint(1, 4)
        
        for dy in range(crack_length):
            cy = crack_y_start + dy
            cx = crack_x + int(np.sin(dy * 0.1) * 5)
            if 0 <= cy < h:
                for ddx in range(-crack_width, crack_width + 1):
                    if 0 <= cx + ddx < w:
                        terrain[cy, cx + ddx] = False
    
    return terrain, waterline_y


def render_scene(terrain, waterline_y):
    """Render the full scene to pixels."""
    w, h = SIZE
    pixels = np.zeros((h, w, 3), dtype=np.float64)
    yy, xx = np.mgrid[0:h, 0:w]
    
    # --- Sky gradient ---
    sky_t = yy.astype(np.float64) / h
    for c in range(3):
        pixels[:, :, c] = SKY_TOP[c] * (1 - sky_t) + SKY_HORIZON[c] * sky_t
    
    # --- Stars in sky ---
    n_stars = 150
    star_x = np.random.randint(0, w, n_stars)
    star_y = np.random.randint(0, int(h * 0.3), n_stars)
    for i in range(n_stars):
        b = np.random.uniform(20, 60)
        pixels[star_y[i], star_x[i]] += b
    
    # --- Ocean ---
    ocean_mask = (yy >= waterline_y) & (~terrain)
    ocean_t = np.clip((yy - waterline_y) / max(1, h - waterline_y), 0, 1)
    
    # Wave texture
    wave_phase = np.random.uniform(0, 2 * np.pi)
    wave1 = np.sin(xx * 0.02 + yy * 0.01 + wave_phase) * 5
    wave2 = np.sin(xx * 0.05 - yy * 0.02 + wave_phase * 1.7) * 3
    wave3 = np.sin(xx * 0.01 + wave_phase * 0.5) * 8 * (1 - ocean_t)
    wave_brightness = wave1 + wave2 + wave3
    
    for c in range(3):
        ocean_color = OCEAN_SURFACE[c] * (1 - ocean_t) + OCEAN_DEEP[c] * ocean_t
        pixels[:, :, c] = np.where(ocean_mask, ocean_color + wave_brightness, pixels[:, :, c])
    
    # --- Rock strata ---
    n_strata = len(STRATA_COLORS)
    rock_top = int(h * 0.25)
    rock_bottom = int(h * 0.90)
    stratum_h = (rock_bottom - rock_top) / n_strata
    
    # Wavy strata boundaries (sine offset per stratum)
    strata_offset = np.zeros((h, w), dtype=np.float64)
    for freq, amp in [(0.005, 15), (0.012, 8), (0.025, 4)]:
        phase = np.random.uniform(0, 2 * np.pi)
        strata_offset += np.sin(xx * freq * 2 * np.pi + phase) * amp
    
    # Which stratum each pixel belongs to
    strata_y = (yy - rock_top + strata_offset) / max(1, stratum_h)
    strata_idx = np.clip(strata_y.astype(int), 0, n_strata - 1)
    strata_frac = np.clip(strata_y - strata_idx, 0, 1)
    next_idx = np.clip(strata_idx + 1, 0, n_strata - 1)
    
    # Build rock color array
    strata_arr = np.array(STRATA_COLORS)
    for c in range(3):
        rock_color = (strata_arr[strata_idx, c] * (1 - strata_frac) +
                     strata_arr[next_idx, c] * strata_frac)
        pixels[:, :, c] = np.where(terrain, rock_color, pixels[:, :, c])
    
    # Rock surface detail: noise texture
    rock_noise = noise_2d(h, w, octaves=4, persistence=0.5, scale=0.015)
    rock_detail = (rock_noise - 0.5) * 25
    for c in range(3):
        pixels[:, :, c] = np.where(terrain, pixels[:, :, c] + rock_detail, pixels[:, :, c])
    
    # --- Cliff edge highlight ---
    # Find left edges of rock (where terrain changes from False to True)
    edge_mask = terrain & ~np.roll(terrain, 1, axis=1)
    edge_mask[:, 0] = False
    
    # Also find top edges
    top_edge = terrain & ~np.roll(terrain, 1, axis=0)
    top_edge[0, :] = False
    
    # Blur edges to create a soft highlight zone
    edge_glow = gaussian_filter((edge_mask | top_edge).astype(np.float64), sigma=2)
    for c in range(3):
        pixels[:, :, c] += edge_glow * 20 * terrain
    
    # --- Weathering darkening on exposed surfaces ---
    # Bottom edges (underside of overhangs) are darker
    bottom_edge = terrain & ~np.roll(terrain, -1, axis=0)
    bottom_glow = gaussian_filter(bottom_edge.astype(np.float64), sigma=4)
    for c in range(3):
        pixels[:, :, c] -= bottom_glow * 15 * terrain
    
    # --- Seafoam at waterline ---
    foam_zone = np.abs(yy - waterline_y) < 12
    near_rock = np.zeros((h, w), dtype=bool)
    for shift in range(1, 20):
        near_rock |= np.roll(terrain, -shift, axis=1)
    
    foam_mask = foam_zone & (~terrain) & near_rock
    foam_noise = noise_2d(h, w, octaves=3, persistence=0.6, scale=0.03)
    foam_strength = np.exp(-((yy - waterline_y) ** 2) / (8 ** 2)) * foam_noise
    
    for c in range(3):
        foam_color = SEAFOAM[c] * 0.4 + FOAM_WHITE[c] * 0.6
        pixels[:, :, c] = np.where(
            foam_mask & (foam_strength > 0.3),
            pixels[:, :, c] * 0.5 + foam_color * 0.5,
            pixels[:, :, c]
        )
    
    # --- Spray/mist near waterline ---
    mist_zone = (np.abs(yy - waterline_y) < 40) & (~terrain)
    mist_noise = noise_2d(h, w, octaves=3, persistence=0.5, scale=0.01)
    mist_strength = np.exp(-((yy - waterline_y) ** 2) / (25 ** 2)) * mist_noise * 0.15
    for c in range(3):
        pixels[:, :, c] = np.where(
            mist_zone,
            pixels[:, :, c] + mist_strength * 60,
            pixels[:, :, c]
        )
    
    # --- Vignette ---
    cx, cy = w / 2, h / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    vignette = 1 - 0.25 * (dist / max_dist) ** 1.8
    for c in range(3):
        pixels[:, :, c] *= vignette
    
    return np.clip(pixels, 0, 255).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.background(8, 18, 32)
    
    print("Building cliff terrain...")
    terrain, waterline_y = build_cliff_and_erode()
    
    print("Rendering scene...")
    pixels = render_scene(terrain, waterline_y)
    
    py5.load_np_pixels()
    actual_h, actual_w = py5.np_pixels.shape[:2]
    
    if actual_h != SIZE[1] or actual_w != SIZE[0]:
        from PIL import Image
        img = Image.fromarray(pixels)
        img = img.resize((actual_w, actual_h), Image.LANCZOS)
        pixels = np.array(img)
    
    py5.np_pixels[:, :, 1] = pixels[:, :, 0]
    py5.np_pixels[:, :, 2] = pixels[:, :, 1]
    py5.np_pixels[:, :, 3] = pixels[:, :, 2]
    py5.update_np_pixels()
    
    print("Done.")


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()
