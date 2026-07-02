from pathlib import Path
import shutil
import subprocess
import sys
import math
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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.02
    
    py5.blend_mode(py5.ADD)
    
    num_rings = 40
    for i in range(num_rings):
        # Calculate depth (z)
        # We want rings to constantly move towards the camera, wrapping around
        z_offset = (i * 100 + py5.frame_count * 5) % (num_rings * 100)
        z = -4000 + z_offset
        
        py5.push_matrix()
        py5.translate(0, 0, z)
        
        # Add some wave motion to the tunnel
        wave_x = math.sin(z * 0.001 + t) * 300
        wave_y = math.cos(z * 0.0015 + t * 0.8) * 300
        py5.translate(wave_x, wave_y, 0)
        
        py5.rotate_z(z * 0.001 + t * 0.5)
        
        # Ring scale
        radius = 500 + math.sin(z * 0.002) * 200
        
        # Color based on depth
        hue = (120 + i * 5 + py5.frame_count) % 360 # Green to Purple
        alpha = py5.remap(z, -4000, 0, 0, 200) # Fade in from distance
        
        # Draw ring of geometry
        num_shapes = 12
        for j in range(num_shapes):
            angle = j * py5.TWO_PI / num_shapes
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            
            py5.push_matrix()
            py5.translate(x, y, 0)
            py5.rotate_z(angle)
            py5.rotate_y(t + j * 0.1)
            py5.rotate_x(t * 1.5 + j * 0.2)
            
            # Glow layers
            py5.fill(hue, 90, 100, alpha * 0.2)
            py5.box(80)
            py5.fill(hue, 100, 100, alpha * 0.8)
            py5.box(40)
            
            # Inner white core
            py5.fill(0, 0, 100, alpha)
            py5.box(15)
            
            py5.pop_matrix()
            
        py5.pop_matrix()
        
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
