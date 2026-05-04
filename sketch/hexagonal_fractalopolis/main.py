from pathlib import Path
import sys
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Logic Lab Path
LOGIC_LAB = Path("/Users/asami/develop/art/logic-lab")
if str(LOGIC_LAB) not in sys.path:
    sys.path.append(str(LOGIC_LAB))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

# Import from logic-lab
try:
    from tiling_patterns.deformation_helpers import deformed_hex_lattice, koch_points, tv08_vertices
except ImportError:
    # Fallback/Mock logic if logic-lab is not accessible as a package
    def hex_vertices(scalar):
        radius = scalar / math.sqrt(3)
        return [(math.cos(2 * math.pi * i / 6) * radius, math.sin(2 * math.pi * i / 6) * radius) for i in range(6)]

    def deformed_hex_lattice(rows, scalar, height, hor):
        base0 = (math.cos(math.pi / 2), math.sin(math.pi / 2))
        base1 = (math.cos(math.pi / 6), math.sin(math.pi / 6))
        cols = math.ceil(rows / (base1[0] - 1 / math.sqrt(3)))
        return [[((base0[0] * i + base1[0] * j) * scalar + hor * scalar * j / math.sqrt(3),
                  ((base0[1] * i + base1[1] * j) * scalar) % (height + scalar))
                 for j in range(cols + 1)] for i in range(rows + 1)]

    def tv08_vertices(scalar, hor, ver):
        vertices = hex_vertices(scalar)
        result = []
        for i, point in enumerate(vertices):
            x, y = point
            if i % 3 == 0:
                x *= 1 + hor
                y *= 1 + hor
            y += (-0.5 if 1 < i < 5 else 0.5) * ver * scalar / math.sqrt(3)
            result.append((x, y))
        return result

    def koch_points(start, end, upper_limit, convex=True, itr=0):
        if itr == upper_limit or itr > 5: return [start, end]
        dx, dy = (end[0] - start[0]) / 3, (end[1] - start[1]) / 3
        angle = math.pi / 3 if convex else -math.pi / 3
        sx = dx * math.cos(angle) - dy * math.sin(angle)
        sy = dx * math.sin(angle) + dy * math.cos(angle)
        pts = [start, (start[0]+dx, start[1]+dy), (start[0]+dx+sx, start[1]+dy+sy), (end[0]-dx, end[1]-dy), end]
        res = []
        for i in range(4):
            seg = koch_points(pts[i], pts[i+1], upper_limit, convex, itr + 1)
            res.extend(seg if not res else seg[1:])
        return res

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 90
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Artwork Constants ---
ROWS = 14
KOCH_DEPTH = 2
STAR_COUNT = 1200

# --- State ---
lattice = None
tile_points = None
star_field = None
scalar = 0

def setup():
    global lattice, tile_points, star_field, scalar
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    scalar = py5.height / ROWS
    hor = 0.15
    ver = 0.2
    
    lattice = deformed_hex_lattice(ROWS + 4, scalar, py5.height, hor)
    
    # Pre-calculate Koch tile points
    vertices = tv08_vertices(scalar, hor, ver)
    tile_points = []
    for i in range(6):
        segment = koch_points(vertices[i], vertices[(i + 1) % 6], KOCH_DEPTH, i < 3)
        tile_points.extend(segment if not tile_points else segment[1:])
    
    # Initialize stars
    star_field = []
    for _ in range(STAR_COUNT):
        star_field.append({
            'pos': (py5.random(py5.width), py5.random(py5.height), py5.random(-500, -100)),
            'size': py5.random(0.5, 2.0),
            'bright': py5.random(40, 100)
        })

def draw():
    py5.background(10) # Near black
    
    # --- Starfield ---
    draw_stars()
    
    # --- Lighting ---
    py5.ambient_light(20, 20, 40)
    py5.directional_light(220, 40, 60, 0.5, 1, -1) # Cyan-ish light
    py5.directional_light(330, 60, 50, -0.5, -0.5, -0.5) # Pink-ish light
    
    # --- Urban Lattice ---
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_x(py5.radians(45))
    py5.rotate_z(py5.frame_count * 0.002)
    
    t = py5.frame_count * 0.01
    
    # Offset to center the tiling
    cx = ROWS * scalar * 0.5
    cy = ROWS * scalar * 0.5
    py5.translate(-cx, -cy)
    
    for i, row in enumerate(lattice):
        for j, point in enumerate(row):
            py5.push_matrix()
            py5.translate(point[0], point[1])
            
            # Mirror logic as per IH02 TV08
            py5.scale(pow(-1, j), 1)
            
            # Height modulation
            h_noise = py5.os_noise(i * 0.2, j * 0.2, t)
            h = 20 + h_noise * 180
            
            # Color based on position and height
            hue = (200 + i * 10 + j * 5 + h_noise * 40) % 360
            sat = 60 + h_noise * 40
            br = 30 + h_noise * 70
            
            # Draw building block (monolithic slab)
            draw_monolith(tile_points, h, hue, sat, br)
            
            py5.pop_matrix()
    
    py5.pop_matrix()
    
    # --- Exit/Preview ---
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def draw_stars():
    py5.push_style()
    py5.no_stroke()
    for star in star_field:
        x, y, z = star['pos']
        # Subtle twinkle
        twinkle = py5.os_noise(x * 0.01, y * 0.01, py5.frame_count * 0.05)
        py5.fill(40, 5, star['bright'] * (0.6 + twinkle * 0.4), 80)
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.circle(0, 0, star['size'])
        py5.pop_matrix()
    py5.pop_style()

def draw_monolith(pts, h, hue, sat, br):
    # Side walls
    py5.stroke(hue, sat, br * 0.5, 60)
    py5.fill(hue, sat, br * 0.3, 90)
    
    # Bottom
    py5.begin_shape()
    for px, py in pts:
        py5.vertex(px, py, 0)
    py5.end_shape(py5.CLOSE)
    
    # Walls
    py5.begin_shape(py5.QUAD_STRIP)
    for px, py in pts:
        py5.vertex(px, py, 0)
        py5.vertex(px, py, h)
    # Close the loop
    py5.vertex(pts[0][0], pts[0][1], 0)
    py5.vertex(pts[0][0], pts[0][1], h)
    py5.end_shape()
    
    # Top face (glowing)
    py5.no_stroke()
    py5.fill(hue, sat, br, 100)
    py5.begin_shape()
    for px, py in pts:
        py5.vertex(px, py, h)
    py5.end_shape(py5.CLOSE)
    
    # Edge glow (optional thin line)
    py5.stroke(hue, 20, 100, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    py5.begin_shape()
    for px, py in pts:
        py5.vertex(px, py, h + 1)
    py5.end_shape(py5.CLOSE)

py5.run_sketch()
