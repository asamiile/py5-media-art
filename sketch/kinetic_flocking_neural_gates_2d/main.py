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

# Particle setup
N_PARTICLES = 300
positions = np.random.rand(N_PARTICLES, 2) * [SIZE[0], SIZE[1]]
velocities = (np.random.rand(N_PARTICLES, 2) - 0.5) * 4
GRID_SIZE = 50

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 0, 20)
    py5.color_mode(py5.RGB, 255)

def draw():
    global positions, velocities
    py5.background(10, 0, 20)
    
    t = py5.frame_count * 0.01
    py5.blend_mode(py5.ADD)
    
    # Update positions based on a curl noise field
    for i in range(N_PARTICLES):
        nx = py5.os_noise(positions[i, 0] * 0.005, positions[i, 1] * 0.005, t) * py5.TWO_PI * 2
        vx = np.cos(nx) * 2
        vy = np.sin(nx) * 2
        
        velocities[i] = velocities[i] * 0.95 + np.array([vx, vy]) * 0.05
        positions[i] += velocities[i]
        
        # Snap to grid force (increases when slow)
        speed = np.linalg.norm(velocities[i])
        if speed < 1.0:
            target_x = np.round(positions[i, 0] / GRID_SIZE) * GRID_SIZE
            target_y = np.round(positions[i, 1] / GRID_SIZE) * GRID_SIZE
            positions[i, 0] += (target_x - positions[i, 0]) * 0.05
            positions[i, 1] += (target_y - positions[i, 1]) * 0.05
            
        # Wrap around screen
        positions[i, 0] = positions[i, 0] % py5.width
        positions[i, 1] = positions[i, 1] % py5.height
    
    # Draw connections
    py5.stroke_weight(2)
    for i in range(N_PARTICLES):
        for j in range(i + 1, N_PARTICLES):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < 120:
                speed_i = np.linalg.norm(velocities[i])
                if speed_i < 0.5:
                    # Rigid white connection
                    py5.stroke(255, 255, 255, py5.remap(dist, 0, 120, 255, 0))
                else:
                    # Organic amber connection
                    py5.stroke(255, 150, 0, py5.remap(dist, 0, 120, 150, 0))
                py5.line(positions[i, 0], positions[i, 1], positions[j, 0], positions[j, 1])

        # Draw particle node
        speed_i = np.linalg.norm(velocities[i])
        if speed_i < 0.5:
            py5.fill(150, 255, 150, 200)
            py5.no_stroke()
            py5.circle(positions[i, 0], positions[i, 1], 6)
        else:
            py5.fill(255, 150, 0, 150)
            py5.no_stroke()
            py5.circle(positions[i, 0], positions[i, 1], 4)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
