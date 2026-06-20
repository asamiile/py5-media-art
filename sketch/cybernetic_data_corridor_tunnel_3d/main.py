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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_FRAMES_TUNNEL = 50

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    speed = 40
    z_offset = (py5.frame_count * speed) % 200
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    for i in range(NUM_FRAMES_TUNNEL):
        z = - (i * 200) + z_offset
        if z > 0:
            continue
            
        # Add curve to the tunnel
        x_shift = py5.sin(t * 0.2 + i * 0.1) * 300
        y_shift = py5.cos(t * 0.15 + i * 0.1) * 300
        
        rot = py5.sin(t * 0.05 + i * 0.05) * py5.PI
        
        hue = (200 + i * 5 + t * 20) % 360
        
        py5.push_matrix()
        py5.translate(x_shift, y_shift, z)
        py5.rotate_z(rot)
        
        # Draw rectangular frame
        py5.stroke(hue, 80, 90, 80)
        s = 800
        py5.rect(-s/2, -s/2, s, s)
        
        # Connect to next frame roughly
        if i < NUM_FRAMES_TUNNEL - 1:
            next_x_shift = py5.sin(t * 0.2 + (i+1) * 0.1) * 300
            next_y_shift = py5.cos(t * 0.15 + (i+1) * 0.1) * 300
            next_z = - ((i+1) * 200) + z_offset
            
            # Un-rotate to draw connection lines in world space
            py5.pop_matrix()
            py5.push_matrix()
            
            py5.stroke(hue, 80, 50, 40)
            py5.stroke_weight(1)
            
            # Connect corners roughly
            for dx, dy in [(-s/2, -s/2), (s/2, -s/2), (s/2, s/2), (-s/2, s/2)]:
                # Current rotated corner
                cx = x_shift + dx * py5.cos(rot) - dy * py5.sin(rot)
                cy = y_shift + dx * py5.sin(rot) + dy * py5.cos(rot)
                
                # Next rotated corner
                next_rot = py5.sin(t * 0.05 + (i+1) * 0.05) * py5.PI
                nx = next_x_shift + dx * py5.cos(next_rot) - dy * py5.sin(next_rot)
                ny = next_y_shift + dx * py5.sin(next_rot) + dy * py5.cos(next_rot)
                
                py5.line(cx, cy, z, nx, ny, next_z)
                
        py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

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
