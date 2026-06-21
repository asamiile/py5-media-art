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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 10000

pos = np.random.uniform(-1000, 1000, (NUM_PARTICLES, 3))
vel = np.zeros((NUM_PARTICLES, 3))
hues = np.random.uniform(200, 260, NUM_PARTICLES)
max_speed = 10.0

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)

def draw():
    global pos, vel
    
    py5.no_stroke()
    py5.fill(0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.01
    
    # Vectorized update
    angle_x = np.sin(pos[:,0]*0.002 + t) * np.pi * 2 + np.cos(pos[:,2]*0.001) * np.pi
    angle_y = np.cos(pos[:,1]*0.002 + t*0.5) * np.pi * 2 + np.sin(pos[:,0]*0.001) * np.pi
    
    force_x = np.cos(angle_x) * np.sin(angle_y)
    force_y = np.sin(angle_x) * np.sin(angle_y)
    force_z = np.cos(angle_y)
    
    force = np.column_stack((force_x, force_y, force_z))
    vel += force * 0.5
    
    speeds = np.linalg.norm(vel, axis=1)
    mask = speeds > max_speed
    vel[mask] = (vel[mask] / speeds[mask][:, np.newaxis]) * max_speed
    
    pos += vel
    
    pos[pos > 1000] = -1000
    pos[pos < -1000] = 1000
    
    # Draw
    py5.camera(
        py5.width/2 + py5.cos(t) * 1500, py5.height/2 + py5.sin(t*0.5) * 500, py5.sin(t) * 1500,
        py5.width/2, py5.height/2, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.2)
    
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for i in range(NUM_PARTICLES):
        hue = (hues[i] + speeds[i] * 5) % 360
        py5.stroke(hue, 80, 80 + speeds[i]*2, 40)
        py5.vertex(pos[i,0], pos[i,1], pos[i,2])
        py5.vertex(pos[i,0]-vel[i,0]*2, pos[i,1]-vel[i,1]*2, pos[i,2]-vel[i,2]*2)
    py5.end_shape()

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

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
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            
        import os
        os._exit(0)

py5.run_sketch()
