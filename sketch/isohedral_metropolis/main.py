from pathlib import Path
import subprocess
import sys
import py5
from math import ceil, cos, pi, sin, sqrt

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

# Tiling Constants
ROWS = 10
SCALAR = 0.0
LATTICE = []
STARS = []

def rotate_pt(pt, angle):
    x, y = pt
    return (x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle))

def add_pts(a, b):
    return (a[0] + b[0], a[1] + b[1])

def sub_pts(a, b):
    return (a[0] - b[0], a[1] - b[1])

def mul_pt(pt, s):
    return (pt[0] * s, pt[1] * s)

def hex_vertices(s):
    radius = s / sqrt(3)
    return [(cos(2 * pi * i / 6) * radius, sin(2 * pi * i / 6) * radius) for i in range(6)]

def hex_lattice(rows, s, h, w):
    base0 = (cos(pi / 2), sin(pi / 2))
    base1 = (cos(pi / 6), sin(pi / 6))
    cols = ceil(w / (base1[0] * s)) + 2
    return [
        [
            ((base0[0] * i + base1[0] * j) * s, ((base0[1] * i + base1[1] * j) * s) % (h + s))
            for j in range(cols + 1)
        ]
        for i in range(rows + 2)
    ]

def parameterize(vertices, i, osc):
    n = len(vertices)
    result = []
    for j in range(2):
        vec = sub_pts(vertices[(i + 1) % n], vertices[i])
        vec = mul_pt(vec, pow(-1, j))
        
        # IH01 symmetry logic: 
        # Edges 0, 1, 2 are independent. 
        # Edges 3, 4, 5 are related to 0, 1, 2 respectively to ensure interlocking.
        idx_j = j if i < 3 else (j + 1) % 2
        angle = osc[i % 3][idx_j] * (pi / 3.5)
        
        result.append(add_pts(rotate_pt(vec, angle), vertices[(i + j) % n]))
    return result

def setup():
    global SCALAR, LATTICE, STARS
    py5.size(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    SCALAR = py5.height / ROWS
    LATTICE = hex_lattice(ROWS, SCALAR, py5.height, py5.width)
    STARS = [(py5.random(py5.width), py5.random(py5.height), py5.random(0.5, 2)) for _ in range(400)]
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(240, 80, 5)

def draw():
    # Persistence fade
    py5.no_stroke()
    py5.fill(240, 80, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Redraw stars
    py5.no_stroke()
    for x, y, s in STARS:
        py5.fill(200, 10, 100, 40)
        py5.circle(x, y, s)
    
    t = py5.frame_count * 0.02
    osc = [
        [sin(t * 1.1 + 0.1), cos(t * 0.9 + 0.5)],
        [sin(t * 0.8 + 1.2), cos(t * 1.3 + 2.1)],
        [sin(t * 1.5 + 0.3), cos(t * 0.7 + 3.4)]
    ]
    
    vertices = hex_vertices(SCALAR)
    
    # Draw Tiling
    for i_lat, row in enumerate(LATTICE):
        for j_lat, pt in enumerate(row):
            py5.push_matrix()
            # Offset to center the lattice better
            py5.translate(pt[0] - SCALAR, pt[1] - SCALAR)
            
            # Base color based on position
            base_hue = (210 + i_lat * 10 + j_lat * 5 + py5.frame_count * 0.1) % 360
            
            # Glow layers for the boundary
            for layer in range(2):
                py5.no_fill()
                py5.stroke_weight(3 - layer * 1.5)
                py5.stroke(base_hue, 80, 100, 20 + layer * 30)
                
                py5.begin_shape()
                py5.vertex(vertices[0][0], vertices[0][1])
                for k in range(len(vertices)):
                    controls = parameterize(vertices, k, osc)
                    end = vertices[(k + 1) % len(vertices)]
                    py5.bezier_vertex(controls[0][0], controls[0][1], controls[1][0], controls[1][1], end[0], end[1])
                py5.end_shape(py5.CLOSE)
            
            # Data Hubs at vertices
            if (i_lat + j_lat) % 4 == 0:
                pulse = (sin(t * 3 + i_lat * 0.7) + 1) * 0.5
                py5.fill(45, 90, 100, 60 * pulse) # Amber
                py5.no_stroke()
                py5.circle(vertices[0][0], vertices[0][1], 2 + 3 * pulse)
            
            py5.pop_matrix()

    # Frame saving and exit logic
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        mid_path = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid_path, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
