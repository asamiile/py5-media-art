from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Define vertices of a Merkaba
r = 300
c30 = np.cos(np.radians(30))
s30 = np.sin(np.radians(30))
v0 = np.array([0, -r, 0])
v1 = np.array([r * c30, r * 1/3, r * s30])
v2 = np.array([-r * c30, r * 1/3, r * s30])
v3 = np.array([0, r * 1/3, -r])

# Upward tetrahedron
tet1 = [v0, v1, v2, v3]
faces1 = [(0,1,2), (0,2,3), (0,3,1), (1,3,2)]

# Downward tetrahedron (inverted)
tet2 = [-v for v in tet1]
faces2 = faces1 # Same connectivity

def rotate_3d(v, rx, ry, rz):
    # Rotate around X
    mx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    # Rotate around Y
    my = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    # Rotate around Z
    mz = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1]
    ])
    
    rotated = mx @ v
    rotated = my @ rotated
    rotated = mz @ rotated
    return rotated

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)

def draw():
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 5, 20, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    rx = t * 0.8
    ry = t * 1.1
    rz = t * 0.5
    
    # Project and draw
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    # Pulsing scale
    scale_factor = 1.0 + 0.2 * np.sin(t * 2.0)
    
    def draw_tet(tet, faces, color_faces, color_edges):
        proj_pts = []
        for v in tet:
            rv = rotate_3d(v * scale_factor, rx, ry, rz)
            # Simple perspective
            z = rv[2]
            f = 800 / (800 - z) if (800 - z) != 0 else 1
            px = rv[0] * f
            py_coord = rv[1] * f
            proj_pts.append((px, py_coord, z))
            
        # Sort faces by depth for simple painter's algorithm
        drawn_faces = []
        for face in faces:
            p0, p1, p2 = [proj_pts[i] for i in face]
            z_avg = (p0[2] + p1[2] + p2[2]) / 3.0
            drawn_faces.append((z_avg, p0, p1, p2))
            
        drawn_faces.sort(key=lambda x: x[0])
        
        for z_avg, p0, p1, p2 in drawn_faces:
            # Faces
            py5.fill(*color_faces)
            py5.no_stroke()
            py5.triangle(p0[0], p0[1], p1[0], p1[1], p2[0], p2[1])
            
            # Edges
            py5.stroke(*color_edges)
            py5.stroke_weight(3)
            py5.no_fill()
            py5.triangle(p0[0], p0[1], p1[0], p1[1], p2[0], p2[1])

    # Tetra 1: Gold
    c_face1 = (255, 200, 50, 30)
    c_edge1 = (255, 200, 50, 200)
    draw_tet(tet1, faces1, c_face1, c_edge1)
    
    # Tetra 2: Cyan
    c_face2 = (50, 200, 255, 30)
    c_edge2 = (50, 200, 255, 200)
    # Give the second tetra a slightly different rotation speed
    global tet2
    draw_tet(tet2, faces1, c_face2, c_edge2)
    
    # Glowing center core
    core_scale = 0.4 + 0.1 * np.sin(t * 4.0)
    py5.no_stroke()
    py5.fill(255, 255, 255, 100)
    py5.circle(0, 0, r * core_scale)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
