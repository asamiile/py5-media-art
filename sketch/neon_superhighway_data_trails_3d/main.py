from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Data packets: x, y, z, speed, length, lane, hue
num_packets = 300
packets = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.blend_mode(py5.ADD)
    
    for _ in range(num_packets):
        lane = random.choice([-3, -2, -1, 1, 2, 3])
        x = lane * 150
        y = 300
        z = random.uniform(-6000, 2000)
        speed = random.uniform(50, 150)
        length = random.uniform(100, 600)
        hue = random.choice([190, 210, 300, 330])
        packets.append([x, y, z, speed, length, lane, hue])

def draw():
    py5.background(240, 80, 5) # Dark navy void
    
    t = py5.frame_count * 0.05
    py5.translate(py5.width / 2, py5.height / 2 - 100, 500)
    
    # Slight camera tilt
    py5.rotate_x(py5.PI / 16)
    
    # Draw perspective grid lines (highway)
    py5.stroke_weight(2)
    for lane in range(-4, 5):
        x = lane * 150
        if lane == 0:
            py5.stroke(200, 50, 100, 80)
        else:
            py5.stroke(220, 80, 60, 40)
        py5.line(x, 300, 2000, x, 300, -8000)
        
    # Draw horizontal grid lines moving towards camera
    speed_grid = (py5.frame_count * 40) % 200
    for i in range(-40, 10):
        z = i * 200 + speed_grid
        py5.stroke(220, 80, 60, py5.remap(z, -8000, 2000, 0, 80))
        py5.line(-600, 300, z, 600, 300, z)
        
    # Draw data packets
    py5.no_stroke()
    for i in range(num_packets):
        p = packets[i]
        x, y, z, speed, length, lane, hue = p
        
        # Move forward
        z += speed
        if z > 2000:
            z = -8000
            hue = random.choice([190, 210, 300, 330])
            
        packets[i][2] = z
        packets[i][6] = hue
        
        # Fade out in the distance
        alpha_val = py5.remap(z, -8000, 2000, 0, 100)
        if alpha_val < 0: alpha_val = 0
        
        py5.fill(hue, 80, 100, alpha_val)
        
        py5.push_matrix()
        py5.translate(x, y - 20, z - length / 2)
        # Data block
        py5.box(20, 40, length)
        py5.pop_matrix()
        
        # Inner brighter core
        py5.fill(0, 0, 100, alpha_val)
        py5.push_matrix()
        py5.translate(x, y - 20, z - length / 2)
        py5.box(10, 20, length * 0.8)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES*100):.1f}%)")

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
