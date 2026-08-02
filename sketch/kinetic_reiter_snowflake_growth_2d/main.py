from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Sketch Identification
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# Size Setup
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Reiter Model Grid Parameters
N = 180  # Grid radius
ROWS = 2 * N + 1
COLS = 2 * N + 1
MID = N
STEPS_PER_FRAME = 1  # 1 step per frame for slow cinematic growth

# Model Coefficients (Dendrite Preset)
ALPHA = 1.0
BETA = 0.35
GAMMA = 0.001

# Simulation State Arrays
s = np.full((ROWS, COLS), BETA, dtype=np.float64)
ice = np.zeros((ROWS, COLS), dtype=bool)
freeze_time = np.zeros((ROWS, COLS), dtype=np.float32)

# Precomputed index arrays
_row_idx = np.arange(ROWS)[:, np.newaxis]
_row_even = _row_idx % 2 == 0

# Screen projection indices
_gx_clipped: np.ndarray
_gy_clipped: np.ndarray
_valid: np.ndarray


def reset_simulation() -> None:
    """Reset state arrays and seed the center crystal."""
    global s, ice, freeze_time
    s.fill(BETA)
    ice.fill(False)
    freeze_time.fill(0.0)
    
    s[MID, MID] = 1.0
    ice[MID, MID] = True
    freeze_time[MID, MID] = 1.0


def hex_neighbor_sum(arr: np.ndarray, pad_val: float) -> np.ndarray:
    """Vectorized sum of 6 hex neighbors on an offset-row grid."""
    p = np.pad(arr, 1, constant_values=pad_val)
    s_even = p[:-2, :-2] + p[:-2, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + p[2:, :-2] + p[2:, 1:-1]
    s_odd = p[:-2, 1:-1] + p[:-2, 2:] + p[1:-1, :-2] + p[1:-1, 2:] + p[2:, 1:-1] + p[2:, 2:]
    return np.where(_row_even, s_even, s_odd)


def simulation_step(frame: int) -> None:
    """Compute one finite-difference step of Reiter's model."""
    global s, ice, freeze_time

    # Determine receptive cells (touching existing ice)
    ice_nb = hex_neighbor_sum(ice.astype(np.float64), 0.0)
    receptive = (ice_nb > 0.0) & ~ice
    
    # Split total mass s into u (diffusable vapor) and v (static ice)
    u = np.zeros_like(s)
    v = np.zeros_like(s)
    
    u[~ice & ~receptive] = s[~ice & ~receptive]
    v[ice | receptive] = s[ice | receptive]

    # Diffuse u for all non-ice cells
    nb_u = hex_neighbor_sum(u, BETA)
    next_u = u.copy()
    non_ice = ~ice
    next_u[non_ice] += ALPHA / 6.0 * (nb_u[non_ice] - 6.0 * u[non_ice])

    # Receptive cells accumulate v by accretion
    next_v = v.copy()
    next_v[receptive] += GAMMA

    # Update total mass s
    s[:] = next_u + next_v

    # Solidify receptive cells where total mass >= 1.0
    new_ice = receptive & (s >= 1.0)
    ice[new_ice] = True
    freeze_time[new_ice] = float(frame)

    # Infinite boundary conditions
    s[[0, -1], :] = BETA
    s[:, [0, -1]] = BETA


def setup() -> None:
    global _gx_clipped, _gy_clipped, _valid
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    pw, ph = py5.pixel_width, py5.pixel_height
    
    # Calculate scale factor for aspect ratio correction
    # Hex height is ROWS * sqrt(3)/2. Fit 94% of screen height.
    scale_factor = (ph * 0.94) / (ROWS * np.sqrt(3) / 2.0)
    
    # Precompute 1D coordinate transformations
    y_coords = np.arange(ph)
    y_grid_float = MID + (y_coords - ph / 2.0) / (scale_factor * np.sqrt(3) / 2.0)
    gy = np.round(y_grid_float).astype(np.int32)
    
    x_coords = np.arange(pw)
    x_grid_float = MID + (x_coords - pw / 2.0) / scale_factor
    
    # Vectorized offset shift for odd rows
    shift = np.where((gy[:, np.newaxis] % 2) != 0, -0.5, 0.0)
    
    # Map to 2D indices
    gx = np.round(x_grid_float[np.newaxis, :] + shift).astype(np.int32)
    gy_2d = np.repeat(gy[:, np.newaxis], pw, axis=1)
    
    # Save valid mask and clipped coordinate matrices
    _valid = (gy_2d >= 0) & (gy_2d < ROWS) & (gx >= 0) & (gx < COLS)
    _gx_clipped = np.clip(gx, 0, COLS - 1)
    _gy_clipped = np.clip(gy_2d, 0, ROWS - 1)
    
    reset_simulation()


def draw() -> None:
    frame = py5.frame_count

    # Execute simulation steps
    for _ in range(STEPS_PER_FRAME):
        simulation_step(frame)

    # Render grid using vectorized pixel mapping
    # Base background (Dark Obsidian: 3, 5, 12)
    r_g = np.full((ROWS, COLS), 3, dtype=np.int32)
    g_g = np.full((ROWS, COLS), 5, dtype=np.int32)
    b_g = np.full((ROWS, COLS), 12, dtype=np.int32)

    # 1. Render vapor density fields as a faint glowing halo around the crystal
    v_norm = np.clip((s - BETA * 0.25) / (1.0 - BETA * 0.25 + 1e-9), 0.0, 1.0)
    r_g[~ice] = np.clip(3 + (v_norm[~ice] * 12).astype(np.int32), 0, 255)
    g_g[~ice] = np.clip(5 + (v_norm[~ice] * 45).astype(np.int32), 0, 255)
    b_g[~ice] = np.clip(12 + (v_norm[~ice] * 95).astype(np.int32), 0, 255)

    # 2. Render ice crystals colored by crystallization time (freeze_time)
    t_freeze = np.clip(freeze_time / float(TOTAL_FRAMES), 0.0, 1.0)
    
    ice_r = np.zeros_like(s, dtype=np.int32)
    ice_g = np.zeros_like(s, dtype=np.int32)
    ice_b = np.zeros_like(s, dtype=np.int32)
    
    mask_early = ice & (t_freeze < 0.6)
    mask_late = ice & (t_freeze >= 0.6)
    
    # Early growth interpolation (0.0 to 0.6): Deep Purple/Magenta -> Electric Cyan
    t_norm_early = t_freeze[mask_early] / 0.6
    ice_r[mask_early] = (80 * (1.0 - t_norm_early) + 0 * t_norm_early).astype(np.int32)
    ice_g[mask_early] = (20 * (1.0 - t_norm_early) + 229 * t_norm_early).astype(np.int32)
    ice_b[mask_early] = (120 * (1.0 - t_norm_early) + 255 * t_norm_early).astype(np.int32)
    
    # Late growth interpolation (0.6 to 1.0): Electric Cyan -> Glacial White
    t_norm_late = (t_freeze[mask_late] - 0.6) / 0.4
    ice_r[mask_late] = (0 * (1.0 - t_norm_late) + 230 * t_norm_late).astype(np.int32)
    ice_g[mask_late] = (229 * (1.0 - t_norm_late) + 250 * t_norm_late).astype(np.int32)
    ice_b[mask_late] = (255 * (1.0 - t_norm_late) + 255 * t_norm_late).astype(np.int32)

    r_g[ice] = ice_r[ice]
    g_g[ice] = ice_g[ice]
    b_g[ice] = ice_b[ice]

    # Map grid elements to 2D screen coordinates
    r_d = r_g[_gy_clipped, _gx_clipped]
    g_d = g_g[_gy_clipped, _gx_clipped]
    b_d = b_g[_gy_clipped, _gx_clipped]

    # Blank out invalid horizontal margin regions
    r_d[~_valid] = 3
    g_d[~_valid] = 5
    b_d[~_valid] = 12

    # Assemble ARGB pixel buffer
    argb = (
        np.int32(-16777216)
        | (r_d.astype(np.int32) << 16)
        | (g_d.astype(np.int32) << 8)
        | b_d.astype(np.int32)
    )

    py5.load_pixels()
    py5.pixels[:] = argb.flatten()
    py5.update_pixels()

    # Fail-safe check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    # Output compilation
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot from the middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
