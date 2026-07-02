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
    py5.background(240, 80, 5) # Dark navy
    
    t = py5.frame_count * 0.03
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    # Pulse based on sin
    pulse = py5.sin(t) * 0.5 + 0.5
    py5.rotate_y(t * 0.5)
    py5.rotate_x(t * 0.3)
    
    num_nodes = 8
    spacing = 150 + pulse * 50
    
    offset = (num_nodes * spacing) / 2
    py5.translate(-offset, -offset, -offset)
    
    for x in range(num_nodes):
        for y in range(num_nodes):
            for z in range(num_nodes):
                dist_to_center = py5.dist(x * spacing, y * spacing, z * spacing, offset, offset, offset)
                max_dist = offset * py5.sqrt(3)
                
                # Only draw if within a spherical radius to form a "heart" or core
                if dist_to_center < max_dist * 0.7:
                    n_val = py5.os_noise(x * 0.1, y * 0.1, z * 0.1 + t)
                    sz = py5.remap(n_val, -1, 1, 5, 25) + pulse * 10
                    
                    hue = (280 + py5.remap(dist_to_center, 0, max_dist, 0, 120) - py5.frame_count) % 360
                    py5.fill(hue, 80, 100, 80)
                    
                    py5.push_matrix()
                    py5.translate(x * spacing, y * spacing, z * spacing)
                    py5.box(sz)
                    
                    # Optional lines connecting nearby points but performance might drop too much,
                    # so we just rely on dense glowing nodes
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
