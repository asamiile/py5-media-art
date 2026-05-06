from pathlib import Path
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

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
PARTICLE_COUNT = 150000
STAR_COUNT = 8000
EINSTEIN_RADIUS = 200
SHADOW_RADIUS = 80

def setup():
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colors, stars, star_colors
    # Nebula particles in a flat plane (background)
    pos = np.random.uniform(-SIZE[0], SIZE[0], (PARTICLE_COUNT, 2))
    
    # Colors based on noise (Teal to Amethyst to Gold)
    # Scale coordinates for noise
    noise_scale = 0.002
    colors = np.zeros((PARTICLE_COUNT, 3))
    for i in range(0, PARTICLE_COUNT, 1000): # Sample noise in chunks for speed
        chunk = pos[i:i+1000]
        for j, p in enumerate(chunk):
            n = py5.noise(p[0] * noise_scale, p[1] * noise_scale)
            if n < 0.4: # Teal
                colors[i+j] = [0, 150, 180]
            elif n < 0.7: # Amethyst
                colors[i+j] = [150, 80, 200]
            else: # Gold
                colors[i+j] = [255, 190, 50]
                
    # Stars (far background)
    stars = np.random.uniform(-SIZE[0], SIZE[0], (STAR_COUNT, 2))
    star_colors = np.random.uniform(200, 255, (STAR_COUNT, 3))

def draw():
    py5.background(5, 5, 15)
    
    time_val = py5.frame_count / 60.0
    
    # Black hole center moves in a slow figure-8
    center_x = SIZE[0]/2 + py5.sin(time_val * 0.4) * 300
    center_y = SIZE[1]/2 + py5.cos(time_val * 0.7) * 150
    center = np.array([center_x, center_y])
    
    # Lensing function (Vectorized NumPy)
    def apply_lensing(points):
        # Displacement from center
        v = points - center
        d2 = np.sum(v**2, axis=1, keepdims=True)
        d = np.sqrt(d2)
        
        # Einstein ring radius squared
        re2 = EINSTEIN_RADIUS**2
        
        # Lensing shift: x' = x + x * Re^2 / |x|^2
        # This is a simplified lensing model
        shift = 1.0 + re2 / (d2 + 1.0) # Avoid division by zero
        lensed_v = v * shift
        
        # Final positions
        lensed_points = center + lensed_v
        
        # Shadow mask: if d < SHADOW_RADIUS, mark as invalid
        mask = d.flatten() > SHADOW_RADIUS
        return lensed_points, mask

    # 1. Warp and Render Starfield
    lensed_stars, star_mask = apply_lensing(stars)
    py5.stroke_weight(1)
    for i in range(STAR_COUNT):
        if star_mask[i]:
            # Subtle twinkling
            alpha = 150 + 100 * py5.noise(stars[i,0], stars[i,1], time_val)
            py5.stroke(*star_colors[i], alpha)
            py5.point(lensed_stars[i,0], lensed_stars[i,1])
            
    # 2. Warp and Render Nebula
    # To speed up, we don't render all particles every frame in preview if needed
    # But for final quality, we render all.
    lensed_pos, pos_mask = apply_lensing(pos)
    
    # Additive blending for the glow
    py5.blend_mode(py5.ADD)
    
    # Use points() for vectorized rendering
    # We'll group by color to minimize stroke calls
    unique_colors = [[0, 150, 180], [150, 80, 200], [255, 190, 50]]
    for col in unique_colors:
        # Mask for this color and valid lensing
        color_mask = np.all(colors == col, axis=1) & pos_mask
        p_to_draw = lensed_pos[color_mask]
        
        if len(p_to_draw) > 0:
            # Varying alpha based on noise for smoky effect
            py5.stroke(*col, 40)
            py5.stroke_weight(2)
            py5.points(p_to_draw)
            
    py5.blend_mode(py5.BLEND)
    
    # 3. Render Event Horizon Shadow
    py5.fill(0)
    py5.no_stroke()
    py5.circle(center_x, center_y, SHADOW_RADIUS * 2)
    
    # 4. Einstein Ring Fringe
    py5.no_fill()
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(2)
    py5.circle(center_x, center_y, EINSTEIN_RADIUS * 2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "10M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
