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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    t = py5.frame_count * 0.03
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_x(t * 0.2)
    py5.rotate_y(t * 0.3)
    
    # Grid dimensions
    grid_size = 800
    steps = 15
    spacing = grid_size / steps
    
    offset = grid_size / 2
    
    for x in range(steps):
        for y in range(steps):
            for z in range(steps):
                px = x * spacing - offset
                py = y * spacing - offset
                pz = z * spacing - offset
                
                # Double layer noise for fluid feeling
                n1 = py5.os_noise(x * 0.1, y * 0.1, z * 0.1 + t * 0.5)
                n2 = py5.os_noise(x * 0.2 + t, y * 0.2, z * 0.2)
                
                # Deform position
                dx = px + py5.sin(n1 * py5.TWO_PI * 2) * 100
                dy = py + py5.cos(n2 * py5.TWO_PI * 2) * 100
                dz = pz + py5.sin((n1 + n2) * py5.TWO_PI) * 100
                
                # Distance to center dictates visibility/color
                dist = py5.dist(dx, dy, dz, 0, 0, 0)
                
                if dist < 600:
                    hue = (200 + n1 * 100 + n2 * 50 + t * 20) % 360
                    alpha = py5.remap(dist, 0, 600, 80, 0)
                    size = py5.remap(n1, 0, 1, 2, 20)
                    
                    py5.push_matrix()
                    py5.translate(dx, dy, dz)
                    py5.fill(hue, 90, 100, alpha)
                    
                    if n2 > 0.7:
                        # Bright sparks
                        py5.fill(0, 0, 100, alpha * 2)
                        py5.sphere_detail(4)
                        py5.sphere(size * 0.5)
                    else:
                        py5.sphere_detail(5)
                        py5.sphere(size)
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
