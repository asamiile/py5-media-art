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
    py5.hint(py5.DISABLE_DEPTH_TEST) # Additive blending for glass effect
    py5.blend_mode(py5.ADD)

def draw():
    py5.background(240, 90, 5) # Very dark navy
    
    t = py5.frame_count * 0.05
    z_offset = py5.frame_count * 20
    
    # Lighting
    py5.point_light(180, 80, 100, 0, 0, z_offset)
    py5.point_light(300, 80, 100, py5.width, py5.height, z_offset + 1000)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Simulate a tunnel
    for i in range(15):
        z = (z_offset + i * 200) % 3000 - 1500
        py5.push_matrix()
        py5.translate(0, 0, z)
        py5.rotate_z(t * 0.1 + i * 0.2)
        
        # Draw glass pillars
        num_pillars = 8
        radius = 800 + py5.sin(t * 0.2 + i) * 200
        for p in range(num_pillars):
            angle = py5.remap(p, 0, num_pillars, 0, py5.TWO_PI)
            x = py5.cos(angle) * radius
            y = py5.sin(angle) * radius
            
            py5.push_matrix()
            py5.translate(x, y, 0)
            py5.rotate_z(angle)
            py5.rotate_x(py5.PI / 4)
            
            hue = (180 + i * 15 + p * 10 + py5.frame_count) % 360
            py5.fill(hue, 80, 90, 20)
            py5.box(100, 600, 100)
            py5.pop_matrix()
            
        py5.pop_matrix()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
