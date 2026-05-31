from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import math
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12  # 12 seconds loop
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
NUM_ROWS = 10
SCALAR = SIZE[1] / (NUM_ROWS - 1)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.stroke_join(py5.ROUND)
    py5.stroke_cap(py5.ROUND)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Precalculate lattice points
    global lattice_points
    lattice_points = []
    
    base0 = (math.cos(math.pi / 2), math.sin(math.pi / 2))
    base1 = (math.cos(math.pi / 6), math.sin(math.pi / 6))
    denom = base1[0]
    cols = int(math.ceil(NUM_ROWS / denom)) + 2
    
    for i in range(-2, NUM_ROWS + 3):
        row_points = []
        for j in range(-2, cols + 3):
            # Hex lattice translation vectors
            x = (base0[0] * i + base1[0] * j) * SCALAR
            y = (base0[1] * i + base1[1] * j) * SCALAR
            row_points.append((x, y, i, j))
        lattice_points.append(row_points)

def get_hex_vertices(scalar):
    radius = scalar / math.sqrt(3)
    return [(math.cos(2 * math.pi * i / 6) * radius, math.sin(2 * math.pi * i / 6) * radius) for i in range(6)]

def sub_pts(a, b):
    return (a[0] - b[0], a[1] - b[1])

def add_pts(a, b):
    return (a[0] + b[0], a[1] + b[1])

def mul_pts(pt, s):
    return (pt[0] * s, pt[1] * s)

def rotate_pt(pt, angle):
    x, y = pt
    return (
        x * math.cos(angle) - y * math.sin(angle),
        x * math.sin(angle) + y * math.cos(angle),
    )

def parameterize(vertices, i, rand):
    n = len(vertices)
    result = []
    for j in range(2):
        vec = sub_pts(vertices[(i + 1) % n], vertices[i])
        vec = mul_pts(vec, pow(-1, j))
        angle = rand[i % 3][j % 2] * math.pi / 3 if i < 3 else rand[i % 3][(j + 1) % 2] * math.pi / 3
        result.append(add_pts(rotate_pt(vec, angle), vertices[(i + j) % n]))
    return result

def draw_deformed_hex(vertices, rand, fill_color, stroke_color, stroke_w):
    py5.fill(fill_color)
    if stroke_w > 0:
        py5.stroke(stroke_color)
        py5.stroke_weight(stroke_w)
    else:
        py5.no_stroke()
        
    py5.begin_shape()
    py5.vertex(vertices[0][0], vertices[0][1])
    for i in range(len(vertices)):
        controls = parameterize(vertices, i, rand)
        end = vertices[(i + 1) % len(vertices)]
        py5.bezier_vertex(
            controls[0][0], controls[0][1],
            controls[1][0], controls[1][1],
            end[0], end[1]
        )
    py5.end_shape(py5.CLOSE)

def draw():
    # Calculate loop parameters
    t = py5.frame_count / TOTAL_FRAMES
    theta = t * 2 * math.pi
    
    # Background
    py5.background(240, 40, 8)  # Obsidian Navy
    
    # Calculate morphing parameters for Heesch tiling (rand)
    # This must be uniform for all tiles so they interlock perfectly
    rand = []
    for i in range(3):
        # Multi-frequency oscillations to create organic motion
        r0 = 0.52 * math.sin(theta + i * (2 * math.pi / 3)) + 0.15 * math.cos(2 * theta - i * 0.8)
        r1 = 0.52 * math.cos(theta - i * (2 * math.pi / 3)) + 0.15 * math.sin(2 * theta + i * 0.8)
        rand.append([r0, r1])
        
    # Get base vertices for a cell
    vertices = get_hex_vertices(SCALAR)
    
    # Draw background grid glow
    py5.blend_mode(py5.ADD)
    
    # Draw tiles with custom coloring
    for row in lattice_points:
        for x, y, i, j in row:
            py5.push_matrix()
            py5.translate(x, y)
            
            # Determine color pattern based on coordinates & time
            # Phase shifts create a rolling wave across the lattice
            dist_center = math.sqrt((x - SIZE[0]/2)**2 + (y - SIZE[1]/2)**2)
            color_phase = theta + (i * 0.25) + (j * 0.18) - (dist_center * 0.001)
            
            # Base pattern hue (cycling between Emerald/Teal (165) and Royal Violet (275))
            hue_mix = (math.sin(color_phase) + 1.0) / 2.0  # 0 to 1
            hue = py5.remap(hue_mix, 0, 1, 165, 275)
            
            # Ambient pulse
            sat = py5.remap(math.cos(color_phase * 1.5), -1, 1, 75, 95)
            val = py5.remap(math.sin(color_phase * 2.0), -1, 1, 65, 88)
            
            # Color accents for specific tiles (Amber Gold)
            is_accent = (i - j) % 7 == 0
            if is_accent:
                # Golden accent
                fill_color = py5.color(45, 95, 95, 85)
                stroke_color = py5.color(45, 80, 100, 95)
            else:
                # Violet/Teal gradient base
                fill_color = py5.color(hue, sat, val, 78)
                stroke_color = py5.color((hue + 15) % 360, sat + 5, 95, 90)
                
            # Draw glow outline first
            draw_deformed_hex(vertices, rand, py5.color(0, 0, 0, 0), stroke_color, 8.0)
            
            # Draw filled tile
            draw_deformed_hex(vertices, rand, fill_color, py5.color(0, 0, 0, 0), 0.0)
            
            py5.pop_matrix()
            
    # Add a foreground overlay of drifting particles to enhance visual depth
    # Particles drift along flow vectors matching the tiling boundary oscillations
    py5.blend_mode(py5.BLEND)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)
            
    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        print("[Render Complete] Video and preview successfully generated.")
        os._exit(0)

py5.run_sketch()
