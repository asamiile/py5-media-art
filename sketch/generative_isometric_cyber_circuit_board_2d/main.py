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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
GRID_SIZE = 80
CELL_SIZE = 40
BOARD_W = GRID_SIZE * CELL_SIZE
BOARD_H = GRID_SIZE * CELL_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 15, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global paths, packets
    
    # Generate random paths on a grid
    num_paths = 1500
    paths = []
    
    for _ in range(num_paths):
        x1 = np.random.randint(-GRID_SIZE//2, GRID_SIZE//2) * CELL_SIZE
        y1 = np.random.randint(-GRID_SIZE//2, GRID_SIZE//2) * CELL_SIZE
        x2 = np.random.randint(-GRID_SIZE//2, GRID_SIZE//2) * CELL_SIZE
        y2 = np.random.randint(-GRID_SIZE//2, GRID_SIZE//2) * CELL_SIZE
        
        # Orthogonal paths: (x1, y1) -> (x2, y1) -> (x2, y2)
        paths.append(((x1, y1), (x2, y1), (x2, y2)))
        
    # Generate data packets traveling along paths
    num_packets = 5000
    packets = []
    
    for _ in range(num_packets):
        path_idx = np.random.randint(0, len(paths))
        speed = np.random.uniform(0.5, 2.0)
        offset = np.random.uniform(0, 1) # Starting position along the path
        color_idx = np.random.randint(0, 3)
        packets.append({"path": path_idx, "speed": speed, "offset": offset, "color": color_idx})

def draw():
    py5.background(5, 8, 12)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Slowly rotating isometric view
    py5.scale(1, 0.5)
    py5.rotate(py5.PI / 4 + np.sin(t * py5.TWO_PI) * 0.1)
    
    # Draw static traces
    py5.stroke(20, 40, 60)
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Draw all paths using beginShape for performance
    # Actually, lines are faster
    
    # We will vectorize the path drawing
    pts = []
    for p in paths:
        (x1, y1), (x2, y1_2), (x2_2, y2) = p
        pts.extend([(x1, y1), (x2, y1_2), (x2, y1_2), (x2_2, y2)])
        
    if pts:
        pts_arr = np.array(pts)
        py5.begin_shape(py5.LINES)
        py5.vertices(pts_arr)
        py5.end_shape()
    
    # Draw data packets
    colors = [
        (0, 255, 200, 200),  # Cyan
        (255, 0, 150, 200),  # Magenta
        (255, 200, 0, 200)   # Yellow
    ]
    
    packet_pts = [[], [], []]
    
    for packet in packets:
        p = paths[packet["path"]]
        (x1, y1), (x2, y1_2), (x2_2, y2) = p
        
        # Calculate lengths
        len1 = abs(x2 - x1)
        len2 = abs(y2 - y1_2)
        total_len = len1 + len2
        if total_len == 0:
            continue
            
        # Current position (wrapping around 0-1)
        progress = (packet["offset"] + t * packet["speed"] * 10) % 1.0
        
        # Map progress to distance
        dist = progress * total_len
        
        if dist < len1:
            # On first segment
            ratio = dist / len1 if len1 > 0 else 0
            cx = x1 + (x2 - x1) * ratio
            cy = y1
        else:
            # On second segment
            dist -= len1
            ratio = dist / len2 if len2 > 0 else 0
            cx = x2
            cy = y1_2 + (y2 - y1_2) * ratio
            
        packet_pts[packet["color"]].append((cx, cy))
        
    # Draw packets by color
    py5.stroke_weight(6)
    for i, c in enumerate(colors):
        if packet_pts[i]:
            py5.stroke(*c)
            py5.begin_shape(py5.POINTS)
            py5.vertices(np.array(packet_pts[i]))
            py5.end_shape()
            
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
