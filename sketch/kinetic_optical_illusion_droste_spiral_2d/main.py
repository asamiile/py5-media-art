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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters for the conformal mapping
NUM_R = 150      # Number of rings in logarithmic space
NUM_THETA = 120  # Number of angular segments

# We will create a grid in the transformed space (u, v)
# u corresponds to ln(r), v corresponds to theta
u_min, u_max = -4.0, 8.0
v_min, v_max = 0, 2 * np.pi

u_grid = np.linspace(u_min, u_max, NUM_R)
v_grid = np.linspace(v_min, v_max, NUM_THETA + 1)

U, V = np.meshgrid(u_grid, v_grid, indexing='ij')

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 10, 15)
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    # We want a seamless loop over 15 seconds (900 frames)
    # The grid in u goes from u_min to u_max. The spacing is du = (u_max - u_min) / (NUM_R - 1)
    # We need to shift u by exactly some integer multiple of the period to loop
    # Actually, a checkerboard repeats when u shifts by 2 tiles
    # So the total translation over TOTAL_FRAMES should be exactly 2 * tile_width in u
    
    t = py5.frame_count / TOTAL_FRAMES # 0 to 1
    
    # Define tile dimensions in transformed space
    # To maintain conformal aspect ratio, du should relate to dv
    dv = (v_max - v_min) / NUM_THETA
    
    # We want the spiral twist to be some integer
    # A Droste-like spiral applies a rotation in complex space: z' = z^(a + i*b)
    # Instead of full complex math, we apply a linear shear in (u,v) space
    twist = 3.0 # Must be integer to connect seamlessly at v=0 and v=2pi
    
    # Animation shift
    shift_u = t * 4.0 * dv # Shift by 4 tiles radially to loop
    shift_v = t * np.pi * 2.0 # Rotate fully
    
    U_anim = U + shift_u
    V_anim = V + shift_v + twist * U
    
    # Map back to cartesian coordinates
    # u = ln(r) -> r = exp(u)
    # v = theta
    
    R = np.exp(U_anim) * 5.0 # Scale factor
    X = R * np.cos(V_anim)
    Y = R * np.sin(V_anim)
    
    py5.no_stroke()
    
    # We draw quads for each cell in the grid
    # To optimize, we use begin_shape(py5.QUADS)
    py5.begin_shape(py5.QUADS)
    
    for i in range(NUM_R - 1):
        for j in range(NUM_THETA):
            # Checkerboard pattern
            # Because of the twist, the logical indices for coloring are slightly different
            # We determine color based on the logical grid before animation shift
            
            # The tile pattern repeats every dv
            logical_u = U[i, j] / dv
            logical_v = V[i, j] / dv
            
            checker = (int(np.floor(logical_u)) + int(np.floor(logical_v))) % 2
            
            if checker == 0:
                py5.fill(250, 240, 230) # Off white
            else:
                py5.fill(20, 25, 30) # Dark grey
            
            # Vertices of the quad
            py5.vertex(X[i, j], Y[i, j])
            py5.vertex(X[i+1, j], Y[i+1, j])
            py5.vertex(X[i+1, j+1], Y[i+1, j+1])
            py5.vertex(X[i, j+1], Y[i, j+1])
            
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
        import os
        os._exit(0)

py5.run_sketch()
