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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)  # Additive blending

def draw():
    py5.background(5, 5, 5)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.05
    
    num_ribbons = 50
    points_per_ribbon = 200
    
    py5.rotate_x(py5.sin(t * 0.2) * 0.5)
    py5.rotate_y(t * 0.5)
    
    for r in range(num_ribbons):
        py5.begin_shape(py5.QUAD_STRIP)
        py5.no_stroke()
        
        hue = (r * (360 / num_ribbons) + t * 50) % 360
        py5.fill(hue, 90, 80, 40)
        
        base_radius = 200 + py5.sin(r * 0.5 + t) * 100
        
        for p in range(points_per_ribbon):
            pt = p / points_per_ribbon
            angle = pt * py5.TWO_PI * 5 + r + t
            
            y = -py5.height * 1.5 + pt * py5.height * 3
            
            # Vortex shape: wider at top and bottom, narrow in middle
            radius = base_radius * (1 + py5.cos(pt * py5.PI * 2)) + p * 2
            
            # Add noise for turbulence
            nx = py5.os_noise(r * 0.1, pt * 5, t * 0.5) * 200
            ny = py5.os_noise(r * 0.1 + 100, pt * 5, t * 0.5) * 200
            nz = py5.os_noise(r * 0.1 + 200, pt * 5, t * 0.5) * 200
            
            x = py5.cos(angle) * radius + nx
            z = py5.sin(angle) * radius + nz
            
            # Ribbon width
            w = 50 + py5.sin(pt * py5.PI * 10 + t * 2) * 30
            
            py5.vertex(x, y + ny, z)
            py5.vertex(x + py5.cos(angle)*w, y + ny, z + py5.sin(angle)*w)
            
        py5.end_shape()

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

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
