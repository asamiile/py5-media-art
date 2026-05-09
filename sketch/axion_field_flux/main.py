from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

# Add project root to path for lib imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# --- Configuration ---
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
NUM_PARTICLES = 240_000
NUM_STARS = 12_000

PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Simulation State ---
# Particle data: pos (3D), phase_offset, speed_factor, hue_base
pos = np.random.uniform(-1000, 1000, (NUM_PARTICLES, 3))
phase_offset = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
speed_factor = np.random.uniform(0.5, 2.0, NUM_PARTICLES)
hue_base = np.random.uniform(0.5, 0.7, NUM_PARTICLES)  # Indigo/Cyan range

# Stars: pos (2D), size, brightness
stars_pos = np.random.uniform(0, 1, (NUM_STARS, 2))
stars_size = np.random.uniform(0.5, 2.5, NUM_STARS)
stars_brightness = np.random.uniform(100, 255, NUM_STARS)


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 1.0, 1.0, 1.0, 1.0)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    t = py5.frame_count / FPS
    py5.background(0.02, 0.02, 0.05)  # Very dark indigo background
    
    # --- 1. Render Starfield (Static background) ---
    py5.push_matrix()
    py5.reset_matrix()
    py5.stroke_weight(1)
    for i in range(0, NUM_STARS, 2000):  # Batching stars for performance
        batch_end = min(i + 2000, NUM_STARS)
        for j in range(i, batch_end):
            py5.stroke(0, 0, 1, stars_brightness[j] / 255)
            py5.point(stars_pos[j, 0] * py5.width, stars_pos[j, 1] * py5.height)
    py5.pop_matrix()

    # --- 2. Update Axion Field Simulation ---
    # Center and rotate for 3D view
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * 0.1)
    py5.rotate_x(np.sin(t * 0.05) * 0.2)

    # Calculate local axion field potential
    # Phi = sin(dist_from_axis * freq + t) + oscillations
    dist_from_z = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)
    # A central "string" tube plus a spatial wave
    phi = np.sin(dist_from_z * 0.01 - t * 2.0) 
    phi += 0.5 * np.sin(pos[:, 2] * 0.005 + t * 1.5)
    
    # Primakoff conversion probability (visibility)
    # Higher near the central string and at specific field phases
    conversion = np.exp(-dist_from_z * 0.002) * (np.sin(phi + phase_offset) + 1) / 2
    
    # Spectral mapping
    # Core (low dist) gets White/Gold, outer gets Indigo/Cyan
    is_core = dist_from_z < 150
    h = np.where(is_core, 0.12 + np.sin(t) * 0.02, hue_base) # Gold vs Indigo/Cyan
    s = np.where(is_core, 0.3, 0.8)
    b = np.where(is_core, 1.0, 0.7)
    a = conversion * 0.6
    
    # Additive blending
    py5.blend_mode(py5.ADD)
    
    # Split into batches for rendering performance
    batch_size = 40000
    for i in range(0, NUM_PARTICLES, batch_size):
        end = min(i + batch_size, NUM_PARTICLES)
        mask = a[i:end] > 0.05 # Optimization: only draw visible particles
        if np.any(mask):
            # We can't easily set individual stroke colors in a single points() call in P3D
            # with differing colors. For high fidelity, we'll group by color/region.
            # But for extreme speed, we use py5.points with a mean color if possible,
            # or loop through slightly larger color buckets.
            
            # Here we'll use a simplified multi-pass for Core vs Field
            core_mask = is_core[i:end] & mask
            field_mask = (~is_core[i:end]) & mask
            
            if np.any(core_mask):
                py5.stroke(0.12, 0.4, 1.0, 0.4) # Gold
                py5.stroke_weight(1.5)
                py5.points(pos[i:end][core_mask])
                
            if np.any(field_mask):
                py5.stroke(0.6, 0.8, 0.7, 0.2) # Cyan/Indigo
                py5.stroke_weight(1.0)
                py5.points(pos[i:end][field_mask])
                
    py5.blend_mode(py5.BLEND)

    # --- 3. Save and Exit ---
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # FFmpeg encoding
        print("\nEncoding video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        
        # Save preview from middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Compression for GitHub (aiming for <100MB)
        print("Compressing video for GitHub...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(SKETCH_DIR / "output.mp4"),
            "-vcodec", "libx264", "-crf", "30", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output_compressed.mp4"),
        ], check=True)
        subprocess.run(["mv", str(SKETCH_DIR / "output_compressed.mp4"), str(SKETCH_DIR / "output.mp4")], check=True)
        
        print("Done.")

if __name__ == "__main__":
    py5.run_sketch()
