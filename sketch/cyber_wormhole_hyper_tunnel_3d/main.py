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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)

def draw():
    py5.background(220, 90, 5) # Deep cyber space
    
    t = py5.frame_count * 0.05
    z_speed = py5.frame_count * 40
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    num_rings = 40
    ring_radius = 600
    
    for i in range(num_rings):
        # Calculate z position to wrap around the camera
        z = ((i * 100 + z_speed) % 4000) - 1000
        
        py5.push_matrix()
        py5.translate(0, 0, z)
        
        # Warp the ring based on noise
        twist = py5.os_noise(i * 0.1, t * 0.2) * py5.TWO_PI
        py5.rotate_z(twist + t * 0.1)
        
        # Draw ring segments
        num_segments = 16
        for j in range(num_segments):
            angle = py5.remap(j, 0, num_segments, 0, py5.TWO_PI)
            
            # Additional warping for radius
            r = ring_radius + py5.os_noise(i * 0.05, j * 0.1, t) * 300
            
            x = py5.cos(angle) * r
            y = py5.sin(angle) * r
            
            py5.push_matrix()
            py5.translate(x, y, 0)
            py5.rotate_z(angle)
            py5.rotate_y(py5.PI / 2)
            
            hue = (160 + i * 5 + j * 10 + py5.frame_count * 2) % 360
            py5.fill(hue, 90, 100, 70)
            
            # Stretch boxes along Z
            py5.box(20, 20, 150)
            py5.pop_matrix()
            
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
