from pathlib import Path
import subprocess
import sys
from math import ceil, cos, pi, sin, sqrt
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

# --- Logic Lab Derived Helpers ---

def hex_vertices(scalar: float) -> list[tuple[float, float]]:
    radius = scalar / sqrt(3)
    return [(cos(2 * pi * i / 6) * radius, sin(2 * pi * i / 6) * radius) for i in range(6)]

def tv08_vertices(scalar: float, hor: float, ver: float) -> list[tuple[float, float]]:
    vertices = hex_vertices(scalar)
    result = []
    for i, (x_val, y_val) in enumerate(vertices):
        if i % 3 == 0:
            x_val *= 1 + hor
            y_val *= 1 + hor
        y_val += (-0.5 if 1 < i < 5 else 0.5) * ver * scalar / sqrt(3)
        result.append((x_val, y_val))
    return result

def deformed_hex_lattice(rows: int, scalar: float, height: float, hor: float) -> list[list[tuple[float, float]]]:
    base0 = (cos(pi / 2), sin(pi / 2))
    base1 = (cos(pi / 6), sin(pi / 6))
    cols = ceil(rows / (base1[0] - 1 / sqrt(3)))
    return [
        [
            (
                (base0[0] * i + base1[0] * j) * scalar + hor * scalar * j / sqrt(3),
                ((base0[1] * i + base1[1] * j) * scalar) % (height + scalar),
            )
            for j in range(cols + 1)
        ]
        for i in range(rows + 1)
    ]

def koch_points(start: tuple[float, float], end: tuple[float, float], upper_limit: int, convex: bool = True, itr: int = 0) -> list[tuple[float, float]]:
    if itr == upper_limit or itr > 3: # Keep depth low for performance in animation
        return [start, end]
    
    def rotate_pt(pt, angle):
        return (pt[0] * cos(angle) - pt[1] * sin(angle), pt[0] * sin(angle) + pt[1] * cos(angle))
    
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    direction = (dx / 3, dy / 3)
    slope = rotate_pt(direction, pi / 3 if convex else -pi / 3)
    
    p1 = (start[0] + direction[0], start[1] + direction[1])
    p2 = (p1[0] + slope[0], p1[1] + slope[1])
    p3 = (end[0] - direction[0], end[1] - direction[1])
    
    points = [start, p1, p2, p3, end]
    result = []
    for i in range(4):
        segment = koch_points(points[i], points[i+1], upper_limit, convex, itr + 1)
        if result:
            result.extend(segment[1:])
        else:
            result.extend(segment)
    return result

# --- Sketch Logic ---

ROWS = 12
SCALAR = 0
STARS = []

def setup():
    global SCALAR, STARS
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    SCALAR = py5.height / ROWS
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate starfield
    for _ in range(2000):
        STARS.append((
            py5.random(-py5.width, py5.width * 2),
            py5.random(-py5.height, py5.height * 2),
            py5.random(-500, 200), # z
            py5.random(0.5, 2.0), # size
            py5.random(80, 200) # alpha
        ))

def draw_starfield():
    py5.push_matrix()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    for x, y, z, s, a in STARS:
        py5.stroke(255, a * (0.7 + 0.3 * sin(py5.frame_count * 0.05 + x)))
        py5.stroke_weight(s)
        py5.point(x, y, z)
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.pop_matrix()

def draw_monolith(i, j, x, y, h, hor, ver, depth):
    py5.push_matrix()
    py5.translate(x, y, 0)
    
    # Vertices for the base (hexagonal)
    base_v = tv08_vertices(SCALAR * 0.7, hor, ver)
    
    # Palette Selection
    # Alternating spectral hubs
    t = py5.frame_count * 0.02
    if (i + j) % 3 == 0:
        hue = (180 + 30 * sin(t + i*0.2)) % 360 # Electric Cyan
    elif (i + j) % 3 == 1:
        hue = (300 + 30 * sin(t + j*0.2)) % 360 # Laser Pink
    else:
        hue = (45 + 15 * sin(t + (i+j)*0.1)) % 360 # Amber Gold

    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    
    # Side walls (layers)
    py5.no_fill()
    num_layers = 4
    for l in range(num_layers):
        lz = l * h / num_layers
        py5.push_matrix()
        py5.translate(0, 0, lz)
        
        inter = l / num_layers
        alpha = 180 * (1 - inter)
        py5.stroke(hue, 200, 255, alpha)
        py5.stroke_weight(1.2)
        
        # Draw hex perimeter (no koch for sides to save performance)
        py5.begin_shape()
        for vx, vy in base_v:
            py5.vertex(vx, vy)
        py5.end_shape(py5.CLOSE)
        py5.pop_matrix()

    # Glowing Cap
    py5.push_matrix()
    py5.translate(0, 0, h)
    
    # Koch fractal detail on the cap
    all_points = []
    for v_idx in range(6):
        segment = koch_points(base_v[v_idx], base_v[(v_idx + 1) % 6], depth, v_idx < 3)
        all_points.extend(segment if not all_points else segment[1:])
    
    # Outer glow line
    py5.stroke(hue, 50, 255, 255)
    py5.stroke_weight(2.5)
    py5.begin_shape()
    for px, py in all_points:
        py5.vertex(px, py)
    py5.end_shape(py5.CLOSE)
    
    # Inner white core
    py5.stroke(255, 255)
    py5.stroke_weight(1)
    py5.begin_shape()
    for px, py in all_points:
        py5.vertex(px, py)
    py5.end_shape(py5.CLOSE)
    
    # Internal infrastructure lines
    if depth > 0:
        py5.stroke(hue, 150, 255, 100)
        py5.stroke_weight(0.8)
        for vx, vy in base_v:
            py5.line(0, 0, 0, vx, vy, 0)
            
    py5.pop_matrix()
    py5.pop_matrix()

def draw():
    py5.background(5, 8, 15)
    
    # View Setup
    py5.camera(py5.width/2, py5.height * 1.1, 700, 
               py5.width/2, py5.height/2, 0, 
               0, 1, 0)
    
    draw_starfield()
    
    # Horizon atmosphere
    py5.push_matrix()
    py5.translate(0, 0, -100)
    py5.no_stroke()
    for i in range(15):
        alpha = 25 * (1 - i/15)
        py5.fill(240, 150, 50, alpha) # Deep violet haze
        py5.rect(-py5.width, -py5.height, py5.width * 3, py5.height * 3)
    py5.pop_matrix()

    # Dynamic deformation
    t = py5.frame_count * 0.02
    hor = 0.15 * sin(t * 0.4)
    ver = 0.1 * cos(t * 0.6)
    
    # Fractal depth pulse
    cycle = py5.frame_count % 180
    koch_depth = 1 if cycle < 40 or (90 < cycle < 130) else 0
    
    lattice = deformed_hex_lattice(ROWS, SCALAR, py5.height, hor)
    
    # Center the lattice on screen
    py5.push_matrix()
    py5.translate(py5.width * 0.05, py5.height * 0.1, 0)
    
    for i, row in enumerate(lattice):
        for j, (lx, ly) in enumerate(row):
            # Noise-driven height
            noise_val = py5.noise(i * 0.15, j * 0.15, t * 0.5)
            h = 80 + 220 * pow(noise_val, 1.5)
            
            # Draw individual monolith
            draw_monolith(i, j, lx, ly, h, hor, ver, koch_depth)
    
    py5.pop_matrix()

    # --- Video & Preview Export ---
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure ffmpeg output is high quality
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Choose a representative frame for preview (midpoint of a cycle)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
