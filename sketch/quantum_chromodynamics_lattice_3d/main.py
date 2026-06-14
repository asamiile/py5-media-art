from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid params
GRID_SIZE = 15
spacing = 40
nodes_pos = None
nodes_base = None
colors = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes_pos, nodes_base, colors
    nodes_pos = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE, 3), dtype=np.float32)
    nodes_base = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE, 3), dtype=np.float32)
    colors = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE, 3), dtype=np.float32)
    
    offset = (GRID_SIZE - 1) * spacing / 2.0
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            for k in range(GRID_SIZE):
                x = i * spacing - offset
                y = j * spacing - offset
                z = k * spacing - offset
                nodes_base[i,j,k] = [x, y, z]
                nodes_pos[i,j,k] = [x, y, z]
                # RGB representation of quantum color charge
                r = 255 if (i+j+k) % 3 == 0 else 50
                g = 255 if (i+j+k) % 3 == 1 else 50
                b = 255 if (i+j+k) % 3 == 2 else 50
                colors[i,j,k] = [r, g, b]

def draw():
    global nodes_pos
    py5.background(5, 5, 10)
    
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    time_val = py5.frame_count * 0.015
    py5.rotate_y(time_val * 0.5)
    py5.rotate_x(time_val * 0.3)
    
    py5.blend_mode(py5.ADD)
    
    # Update positions with 4D noise
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            for k in range(GRID_SIZE):
                bx, by, bz = nodes_base[i,j,k]
                
                # Boiling effect
                nx = py5.os_noise(bx*0.01, by*0.01, bz*0.01, time_val) * 2 - 1
                ny = py5.os_noise(bx*0.01 + 100, by*0.01, bz*0.01, time_val) * 2 - 1
                nz = py5.os_noise(bx*0.01, by*0.01 + 100, bz*0.01, time_val) * 2 - 1
                
                intensity = py5.os_noise(bx*0.02, by*0.02, bz*0.02, time_val * 2) * 60
                
                nodes_pos[i,j,k,0] = bx + nx * intensity
                nodes_pos[i,j,k,1] = by + ny * intensity
                nodes_pos[i,j,k,2] = bz + nz * intensity

    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw connections
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            for k in range(GRID_SIZE):
                p1 = nodes_pos[i,j,k]
                c1 = colors[i,j,k]
                
                # draw the particle
                py5.push_matrix()
                py5.translate(p1[0], p1[1], p1[2])
                py5.stroke(c1[0], c1[1], c1[2], 200)
                py5.point(0, 0)
                py5.pop_matrix()
                
                # draw lines to neighbors if close enough (simulating strong force snapping)
                if i < GRID_SIZE - 1:
                    p2 = nodes_pos[i+1,j,k]
                    d = np.linalg.norm(p1 - p2)
                    if d < spacing * 1.5:
                        py5.stroke(c1[0], c1[1], c1[2], 100)
                        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
                        
                if j < GRID_SIZE - 1:
                    p2 = nodes_pos[i,j+1,k]
                    d = np.linalg.norm(p1 - p2)
                    if d < spacing * 1.5:
                        py5.stroke(c1[0], c1[1], c1[2], 100)
                        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
                        
                if k < GRID_SIZE - 1:
                    p2 = nodes_pos[i,j,k+1]
                    d = np.linalg.norm(p1 - p2)
                    if d < spacing * 1.5:
                        py5.stroke(c1[0], c1[1], c1[2], 100)
                        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
                        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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
            print("[Render Cleanup] Temporary frames directory removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
