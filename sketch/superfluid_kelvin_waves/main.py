from pathlib import Path
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_FILAMENTS = 5
NUM_POINTS_PER_FILAMENT = 200
NUM_TRACERS = 80000

# Filament points
z_coords = np.linspace(-500, 500, NUM_POINTS_PER_FILAMENT)
theta = np.linspace(0, 4 * np.pi, NUM_POINTS_PER_FILAMENT)

# Tracer positions
TRACER_POS = np.random.uniform(-400, 400, (NUM_TRACERS, 3))

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(10, 5, 20)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global TRACER_POS
    t = py5.frame_count
    
    py5.background(5, 5, 15)
    
    # Filament Physics: Kelvin Waves
    filaments = []
    for i in range(NUM_FILAMENTS):
        # Base position
        offset_x = 200 * np.cos(i * 2 * np.pi / NUM_FILAMENTS + t * 0.01)
        offset_y = 200 * np.sin(i * 2 * np.pi / NUM_FILAMENTS + t * 0.01)
        
        # Helical perturbation
        amp = 30 + 10 * np.sin(t * 0.05 + i)
        freq = 3.0
        phase = t * 0.15 + i * 0.5
        
        px = offset_x + amp * np.cos(freq * z_coords * 0.01 + phase)
        py = offset_y + amp * np.sin(freq * z_coords * 0.01 + phase)
        pz = z_coords
        
        filaments.append(np.stack([px, py, pz], axis=-1))
    
    # Tracer motion: simple flow around closest filament
    for fil in filaments:
        # Distance to filament points (sampled)
        # Using a simplified attraction/rotation
        rel = TRACER_POS[:, np.newaxis, :] - fil[::10]
        dist_sq = np.sum(rel**2, axis=-1)
        min_idx = np.argmin(dist_sq, axis=1)
        
        # Closest relative vector
        closest_rel = rel[np.arange(NUM_TRACERS), min_idx]
        d = np.sqrt(dist_sq[np.arange(NUM_TRACERS), min_idx])
        
        # Velocity: Rotation around the filament + drift
        v_rot = np.cross(closest_rel, [0, 0, 1]) / (d[:, np.newaxis] + 10) * 15
        TRACER_POS += v_rot * 0.5
        
    # Wrapping
    TRACER_POS = (TRACER_POS + 500) % 1000 - 500
    
    # Rendering
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * 0.005)
    
    py5.blend_mode(py5.ADD)
    
    # Draw Filaments
    py5.no_fill()
    py5.stroke_weight(3.0)
    for i, fil in enumerate(filaments):
        py5.stroke(200, 200, 255, 150)
        py5.begin_shape()
        for p in fil[::2]:
            py5.vertex(*p)
        py5.end_shape()
        
    # Draw Tracers
    py5.stroke_weight(1.5)
    # Color mapping: Ultra Violet (280) to Silver
    py5.stroke(180, 150, 255, 40)
    py5.points(TRACER_POS[::2])
    
    py5.stroke(220, 220, 255, 30)
    py5.points(TRACER_POS[1::2])
    
    py5.pop_matrix()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
