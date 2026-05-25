from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Basic physics state
num_nodes = 120
positions = None
velocities = None

def setup():
    global positions, velocities
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(5, 15, 20)  # Deep teal/black
    FRAMES_DIR.mkdir(exist_ok=True)
    
    import numpy as np
    # Initialize in a tight cluster in the center
    positions = np.random.randn(num_nodes, 2) * 50 + [py5.width/2, py5.height/2]
    velocities = np.zeros((num_nodes, 2))

def draw():
    global positions, velocities
    import numpy as np
    
    py5.push_style()
    py5.fill(5, 15, 20, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_style()

    # Physics step
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dist = np.linalg.norm(diff, axis=-1)
    
    # Avoid division by zero
    np.fill_diagonal(dist, np.inf)
    
    # Forces: repulsion at short range, attraction at medium range
    force_mag = np.where(dist < 80, -200 / (dist**2 + 1), 0)
    force_mag += np.where((dist >= 80) & (dist < 200), 0.5, 0)
    
    # Center attraction to keep them from flying off
    center_dist = positions - [py5.width/2, py5.height/2]
    velocities -= center_dist * 0.001
    
    force_dir = diff / (dist[..., np.newaxis] + 1e-5)
    force_vectors = np.sum(force_dir * force_mag[..., np.newaxis], axis=1)
    
    velocities += force_vectors * 0.1
    # Add some organic noise/wobble
    time_offset = py5.frame_count * 0.02
    wobble = np.array([
        [py5.noise(i * 0.1, time_offset), py5.noise(i * 0.1, time_offset + 100)] 
        for i in range(num_nodes)
    ]) * 2 - 1
    velocities += wobble * 0.5
    
    velocities *= 0.85 # Damping
    positions += velocities
    
    py5.blend_mode(py5.ADD)
    
    # Draw connections
    py5.stroke_weight(2)
    for i in range(num_nodes):
        # Draw node body
        pulse = py5.sin(py5.frame_count * 0.05 + i) * 0.5 + 0.5
        
        py5.no_stroke()
        if i % 10 == 0:
            py5.fill(255, 100, 0, 150) # Orange accent
            py5.circle(positions[i, 0], positions[i, 1], 8 + pulse * 6)
        else:
            py5.fill(50, 255, 150, 100) # Bioluminescent green
            py5.circle(positions[i, 0], positions[i, 1], 12 + pulse * 8)
            
        # Draw webs
        py5.stroke(50, 200, 255, 40) # Pale cyan web
        for j in range(i+1, num_nodes):
            if dist[i, j] < 150:
                py5.line(positions[i, 0], positions[i, 1], positions[j, 0], positions[j, 1])
                
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
