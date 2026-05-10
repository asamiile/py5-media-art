import numpy as np
import py5
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Lattice definition
GRID_SIZE = 12
SPACING = 60

# Monopoles: [x, y, z, tx, ty, tz, active]
NUM_MONOPOLES = 80
monopoles = np.zeros((NUM_MONOPOLES, 7), dtype=np.float32)

MAX_STRINGS = 30000
dirac_strings = np.zeros((MAX_STRINGS, 7), dtype=np.float32)
string_count = 0

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    global monopoles
    for i in range(NUM_MONOPOLES):
        x = np.random.randint(-GRID_SIZE, GRID_SIZE) * SPACING
        y = np.random.randint(-GRID_SIZE, GRID_SIZE) * SPACING
        z = np.random.randint(-GRID_SIZE, GRID_SIZE) * SPACING
        monopoles[i, 0:3] = [x, y, z]
        monopoles[i, 3:6] = [x, y, z]
        monopoles[i, 6] = 1

def pick_next_target(pos):
    dx = np.random.choice([-SPACING, SPACING])
    dy = np.random.choice([-SPACING, SPACING])
    dz = np.random.choice([-SPACING, SPACING])
    
    nx = np.clip(pos[0] + dx, -GRID_SIZE * SPACING, GRID_SIZE * SPACING)
    ny = np.clip(pos[1] + dy, -GRID_SIZE * SPACING, GRID_SIZE * SPACING)
    nz = np.clip(pos[2] + dz, -GRID_SIZE * SPACING, GRID_SIZE * SPACING)
    return np.array([nx, ny, nz], dtype=np.float32)

def add_string(x1, y1, z1, x2, y2, z2):
    global dirac_strings, string_count
    if string_count < MAX_STRINGS:
        dirac_strings[string_count] = [x1, y1, z1, x2, y2, z2, 100.0]
        string_count += 1
    else:
        # replace oldest
        idx = np.argmin(dirac_strings[:, 6])
        dirac_strings[idx] = [x1, y1, z1, x2, y2, z2, 100.0]

def draw():
    global monopoles, dirac_strings, string_count
    
    py5.background(240, 100, 5)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    # Outer structure
    py5.stroke(190, 80, 70, 15)
    py5.stroke_weight(2)
    py5.no_fill()
    s = SPACING * GRID_SIZE
    py5.box(s*2)
    
    # Update and draw monopoles
    py5.stroke(45, 100, 100, 100)
    py5.stroke_weight(8)
    pts = []
    
    for i in range(NUM_MONOPOLES):
        curr = monopoles[i, 0:3]
        target = monopoles[i, 3:6]
        
        diff = target - curr
        dist = np.linalg.norm(diff)
        
        if dist < 2.0:
            curr[:] = target[:]
            next_t = pick_next_target(curr)
            monopoles[i, 3:6] = next_t
            add_string(curr[0], curr[1], curr[2], next_t[0], next_t[1], next_t[2])
        else:
            curr += diff * 0.15
            
        pts.append(curr.copy())
        
    pts = np.array(pts)
    py5.points(pts)
    
    py5.stroke(45, 100, 100, 30)
    py5.stroke_weight(25)
    py5.points(pts)
    
    # Update and draw dirac strings
    if string_count > 0:
        dirac_strings[:string_count, 6] -= 0.6
        active_idx = np.where(dirac_strings[:string_count, 6] > 0)[0]
        
        if len(active_idx) > 0:
            active_strings = dirac_strings[active_idx]
            
            # Batch drawing by age for performance and correct alpha
            ages = active_strings[:, 6]
            
            # 3 age buckets
            b1 = active_strings[ages > 70]
            b2 = active_strings[(ages <= 70) & (ages > 30)]
            b3 = active_strings[ages <= 30]
            
            if len(b3) > 0:
                py5.stroke(320, 100, 90, 30)
                py5.stroke_weight(2)
                lines3 = np.empty((len(b3), 6), dtype=np.float32)
                lines3[:, 0:3] = b3[:, 0:3]
                lines3[:, 3:6] = b3[:, 3:6]
                py5.lines(lines3)
                
            if len(b2) > 0:
                py5.stroke(320, 100, 90, 60)
                py5.stroke_weight(3)
                lines2 = np.empty((len(b2), 6), dtype=np.float32)
                lines2[:, 0:3] = b2[:, 0:3]
                lines2[:, 3:6] = b2[:, 3:6]
                py5.lines(lines2)
                
            if len(b1) > 0:
                py5.stroke(320, 100, 90, 100)
                py5.stroke_weight(4)
                lines1 = np.empty((len(b1), 6), dtype=np.float32)
                lines1[:, 0:3] = b1[:, 0:3]
                lines1[:, 3:6] = b1[:, 3:6]
                py5.lines(lines1)
                
                # Inner bright core
                py5.stroke(0, 0, 100, 100)
                py5.stroke_weight(1.5)
                py5.lines(lines1)
                
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
