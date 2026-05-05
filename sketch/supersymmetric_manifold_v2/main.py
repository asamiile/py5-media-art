from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

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

# Pre-calculate star positions for consistency
NUM_STARS = 2000
stars = np.random.rand(NUM_STARS, 3) # x, y, size

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # Subtle decay background for trails
    # To keep it "clean" for MP4, we draw a dark rect with alpha
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.no_stroke()
    py5.fill(2, 4, 12, 15) # Dark navy with alpha for trailing
    py5.rect(0, 0, py5.width, py5.height)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    # Draw starfield (static)
    py5.stroke_weight(1)
    for i in range(NUM_STARS):
        s = stars[i]
        alpha = 100 + 155 * np.sin(py5.frame_count * 0.05 + i)
        py5.stroke(200, 220, 255, alpha * 0.5)
        py5.point(s[0] * py5.width, s[1] * py5.height)

    t = py5.frame_count / TOTAL_FRAMES
    
    # Parameters for the manifold
    # We modulate these over time for the "breath" effect
    m = 4 + 2 * np.sin(py5.TWO_PI * t)
    n1 = 1.0 + 0.5 * np.cos(py5.TWO_PI * t * 2)
    n2 = 1.0 + 0.3 * np.sin(py5.TWO_PI * t * 1.5)
    n3 = n2
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * py5.TWO_PI)
    py5.rotate_x(t * py5.TWO_PI * 0.5)
    py5.rotate_z(t * py5.TWO_PI * 0.2)
    
    # Generate points for the manifold
    num_points = 1000
    phi = np.linspace(-np.pi, np.pi, num_points)
    
    # Superformula R
    a, b = 1, 1
    t1 = np.abs(np.cos(m * phi / 4) / a)**n2
    t2 = np.abs(np.sin(m * phi / 4) / b)**n3
    r = (t1 + t2)**(-1 / n1)
    
    # Scale and center
    scale = 300 + 50 * np.sin(py5.TWO_PI * t * 3)
    x = r * np.cos(phi) * scale
    y = r * np.sin(phi) * scale
    
    # Draw layered shells with spectral colors
    num_shells = 8
    for i in range(num_shells):
        z_off = (i - num_shells/2) * 20 * np.sin(py5.TWO_PI * t)
        
        # Color: transition between Electric Indigo, Cyan, and Magenta
        hue = (t * 255 + i * 20) % 255
        py5.stroke_weight(1.5)
        py5.no_fill()
        
        # Draw as a silken web
        py5.begin_shape()
        for j in range(num_points):
            # Add subtle jitter for the "shimmer"
            jx = x[j] + np.sin(t * 10 + j * 0.1 + i) * 5
            jy = y[j] + np.cos(t * 12 + j * 0.1 + i) * 5
            
            # Map hue to RGB (manual to avoid colorMode state issues)
            # Roughly: 0=Violet, 85=Cyan, 170=Magenta
            if i % 3 == 0:
                py5.stroke(148, 0, 211, 100) # Violet
            elif i % 3 == 1:
                py5.stroke(0, 255, 255, 100) # Cyan
            else:
                py5.stroke(255, 0, 255, 100) # Magenta
                
            py5.vertex(jx, jy, z_off)
        py5.end_shape(py5.CLOSE)

    py5.pop_matrix()

    # Save frames and encode
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", # High quality
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Use a frame from the middle as preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
