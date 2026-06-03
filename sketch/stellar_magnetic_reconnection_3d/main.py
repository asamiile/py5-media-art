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

# Parameters
NUM_POINTS = 300
RADIUS = 400

# State
points = []
base_positions = []
velocities = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize points on a sphere
    phi = np.arccos(1 - 2 * np.random.rand(NUM_POINTS))
    theta = 2 * np.pi * np.random.rand(NUM_POINTS)
    
    for i in range(NUM_POINTS):
        x = RADIUS * np.sin(phi[i]) * np.cos(theta[i])
        y = RADIUS * np.sin(phi[i]) * np.sin(theta[i])
        z = RADIUS * np.cos(phi[i])
        points.append(np.array([x, y, z]))
        base_positions.append(np.array([x, y, z]))
        velocities.append(np.array([0.0, 0.0, 0.0]))

def draw():
    py5.background(0)
    
    # Additive blending setup
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera and lighting
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.002)
    
    t = py5.frame_count * 0.01
    
    # Update points
    for i in range(NUM_POINTS):
        bp = base_positions[i]
        # Add some noise-based drift
        nx = py5.os_noise(bp[0]*0.005, bp[1]*0.005, t) * 2 - 1
        ny = py5.os_noise(bp[1]*0.005, bp[2]*0.005, t) * 2 - 1
        nz = py5.os_noise(bp[2]*0.005, bp[0]*0.005, t) * 2 - 1
        
        drift = np.array([nx, ny, nz]) * 150
        target = bp + drift
        
        velocities[i] += (target - points[i]) * 0.05
        velocities[i] *= 0.9  # damping
        points[i] += velocities[i]
        
    # Draw field lines (reconnections)
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Find neighbors and draw curves
    for i in range(NUM_POINTS):
        p1 = points[i]
        
        # draw point
        py5.stroke(255, 200, 50, 150)
        py5.push_matrix()
        py5.translate(*p1)
        py5.box(2)
        py5.pop_matrix()
        
        # Connect to nearest neighbors
        distances = []
        for j in range(NUM_POINTS):
            if i != j:
                d = np.linalg.norm(p1 - points[j])
                distances.append((d, j))
        
        distances.sort(key=lambda x: x[0])
        
        for k in range(3): # Connect to 3 nearest
            d, j = distances[k]
            if d < 300: # Max connection distance
                p2 = points[j]
                
                # Tension determines color and curve
                tension = d / 300.0
                
                if tension > 0.9:
                    # About to snap - blinding white/yellow
                    py5.stroke(255, 255, 200, 200)
                    py5.stroke_weight(4)
                elif tension > 0.6:
                    # High tension - solar flare orange
                    py5.stroke(255, 100, 0, 100)
                    py5.stroke_weight(2)
                else:
                    # Low tension - deep crimson
                    py5.stroke(150, 0, 0, 50)
                    py5.stroke_weight(1)
                
                # Draw bezier curve bowing outward from the origin
                cp1 = p1 * 1.2
                cp2 = p2 * 1.2
                
                py5.bezier(p1[0], p1[1], p1[2],
                           cp1[0], cp1[1], cp1[2],
                           cp2[0], cp2[1], cp2[2],
                           p2[0], p2[1], p2[2])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
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
