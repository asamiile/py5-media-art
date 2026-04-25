from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Distant world" — a planet seen from space via analytic ray-sphere
# intersection; surface colored by multi-octave noise, atmospheric glow at limb

SPHERE_R = 0.36    # sphere radius in normalized canvas units (height = 1.0)
SPHERE_CX = 0.50   # center x (fraction of width)
SPHERE_CY = 0.50   # center y (fraction of height)

# Light direction (normalized)
LIGHT = np.array([0.55, 0.70, 0.42], dtype=np.float32)
LIGHT /= np.linalg.norm(LIGHT)

# Palette
SPACE_COL = np.array([2,    3,   8], dtype=np.float32)   # deep space
ATMO_COL  = np.array([60, 140, 200], dtype=np.float32)   # atmospheric blue-cyan
LAND_COLS = np.array([
    [60,  90,  60],   # ocean deep (lowest terrain)
    [80, 130,  90],   # shallow sea / coastal
    [140, 160, 100],  # lowland plains
    [160, 130,  80],  # highlands
    [120,  80,  50],  # mountain rust
    [220, 215, 210],  # snow peaks
], dtype=np.float32)

pixels_arr = None


def fbm(x, y, z, octaves=6):
    """Fractional Brownian motion via summed sine/cos harmonics (no scipy)."""
    freq = 2.8
    amp = 1.0
    total = 0.0
    for _ in range(octaves):
        total += amp * (
            np.sin(freq * x + 1.3) * np.cos(freq * y - 0.7) +
            np.sin(freq * y + 2.1) * np.cos(freq * z + 0.4) +
            np.sin(freq * z - 1.1) * np.cos(freq * x + 1.8)
        )
        freq *= 2.07
        amp  *= 0.48
    return total


def terrain_color(height):
    """Map terrain height (−1..1) to a color using LAND_COLS stops."""
    n = len(LAND_COLS)
    # Remap −1..1 → 0..n−1
    t = (height + 1.0) / 2.0 * (n - 1)
    t = np.clip(t, 0, n - 1 - 1e-6)
    lo = t.astype(int)
    hi = np.minimum(lo + 1, n - 1)
    f = (t - lo)[..., np.newaxis]
    return LAND_COLS[lo] * (1 - f) + LAND_COLS[hi] * f


def setup():
    global pixels_arr
    py5.size(*SIZE)

    # Work at 1/2 resolution then upscale 2× for speed
    W2, H2 = SIZE[0] // 2, SIZE[1] // 2

    # Canvas aspect ratio: W/H
    aspect = SIZE[0] / SIZE[1]

    # Build UV grid for ray directions (perspective-free orthographic projection)
    u = np.linspace(0, 1, W2, dtype=np.float32)  # x: 0→1
    v = np.linspace(0, 1, H2, dtype=np.float32)  # y: 0→1
    U, V = np.meshgrid(u, v)

    # Sphere center and radius in canvas coords
    cx, cy = SPHERE_CX, SPHERE_CY
    r = SPHERE_R

    # Ray from camera (orthographic) — dx, dy in canvas space
    dx = (U - cx) * aspect
    dy = V - cy

    dist2 = dx * dx + dy * dy   # squared dist from sphere center (in projected plane)
    r2 = r * r

    on_sphere = dist2 <= r2

    # Surface point z (depth into sphere) for pixels that hit
    dz_sq = np.where(on_sphere, r2 - dist2, 0.0)
    dz = np.sqrt(np.maximum(dz_sq, 0.0))   # positive z = facing camera

    # Surface normal at each sphere pixel
    nx_s = dx / r
    ny_s = dy / r
    nz_s = dz / r

    # Diffuse lighting
    ndotl = np.clip(nx_s * LIGHT[0] + ny_s * LIGHT[1] + nz_s * LIGHT[2], 0, 1)
    ambient = 0.08

    # Surface texture via fbm applied to 3D sphere surface position
    sx = nx_s  # already normalized surface coords
    sy = ny_s
    sz = nz_s
    height = fbm(sx, sy, sz, octaves=7)
    height_norm = np.tanh(height * 0.8)   # compress to −1..1

    # Terrain color
    land = terrain_color(height_norm)   # (H2, W2, 3)

    # Shading
    light_factor = ambient + ndotl * (1 - ambient)
    shaded = land * light_factor[..., np.newaxis]

    # Atmosphere: glow near the limb (edge of sphere)
    # limb_t goes 0 at center to 1 at edge
    limb_dist = np.sqrt(np.maximum(dist2, 0.0)) / r   # 0→1 from center to limb
    atmo_strength = np.exp(-10 * (1 - limb_dist) ** 2) * 0.85   # peaks at limb
    atmo_strength_halo = np.exp(-8 * np.maximum(limb_dist - 1, 0) ** 2 * (1/0.04))

    # Final compositing
    r_ch = np.where(on_sphere,
                    np.clip(shaded[..., 0] + ATMO_COL[0] * atmo_strength * 0.4, 0, 255),
                    SPACE_COL[0] + ATMO_COL[0] * atmo_strength_halo * 0.7)
    g_ch = np.where(on_sphere,
                    np.clip(shaded[..., 1] + ATMO_COL[1] * atmo_strength * 0.4, 0, 255),
                    SPACE_COL[1] + ATMO_COL[1] * atmo_strength_halo * 0.7)
    b_ch = np.where(on_sphere,
                    np.clip(shaded[..., 2] + ATMO_COL[2] * atmo_strength * 0.5, 0, 255),
                    SPACE_COL[2] + ATMO_COL[2] * atmo_strength_halo * 0.9)

    # Stars (random) in space background
    rng = np.random.default_rng(77)
    n_stars = 800
    st_x = rng.integers(0, W2, n_stars)
    st_y = rng.integers(0, H2, n_stars)
    st_b = rng.integers(100, 220, n_stars)
    for i in range(n_stars):
        if not on_sphere[st_y[i], st_x[i]]:
            r_ch[st_y[i], st_x[i]] = st_b[i]
            g_ch[st_y[i], st_x[i]] = st_b[i]
            b_ch[st_y[i], st_x[i]] = min(255, st_b[i] + 20)

    img = np.stack([
        np.clip(r_ch, 0, 255).astype(np.uint8),
        np.clip(g_ch, 0, 255).astype(np.uint8),
        np.clip(b_ch, 0, 255).astype(np.uint8),
    ], axis=-1)

    # Upscale 2× with repeat
    img_full = np.repeat(np.repeat(img, 2, axis=0), 2, axis=1)

    alpha = np.full((SIZE[1], SIZE[0]), 255, dtype=np.uint8)
    pixels_arr = np.stack([alpha, img_full[..., 0], img_full[..., 1], img_full[..., 2]], axis=-1)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    if pixels_arr.shape[0] == h and pixels_arr.shape[1] == w:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)
    py5.update_np_pixels()

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()
