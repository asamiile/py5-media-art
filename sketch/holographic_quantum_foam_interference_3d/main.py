from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Precompute grid
grid_size = 40
spacing = 20
offset = grid_size * spacing / 2

x_idx, y_idx, z_idx = np.mgrid[0:grid_size, 0:grid_size, 0:grid_size]
px = x_idx * spacing - offset
py = y_idx * spacing - offset
pz = z_idx * spacing - offset

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.rotate_x(t * py5.TWO_PI * 0.5)
    py5.rotate_y(t * py5.TWO_PI * 0.3)
    
    py5.blend_mode(py5.ADD)
    
    # Vectorized calculation
    val1 = np.sin(x_idx * 0.2 + t * py5.TWO_PI) * np.cos(y_idx * 0.3 - t * py5.PI)
    val2 = np.cos(z_idx * 0.25 + t * py5.TWO_PI) * np.sin(x_idx * 0.15 + y_idx * 0.15)
    
    interference = val1 + val2
    mask = interference > 0.8
    
    active_px = px[mask]
    active_py = py[mask]
    active_pz = pz[mask]
    active_i = interference[mask]
    
    for i in range(len(active_px)):
        val = active_i[i]
        py5.push_matrix()
        py5.translate(float(active_px[i]), float(active_py[i]), float(active_pz[i]))
        s = (val - 0.8) * 15
        
        if val > 1.4:
            py5.fill(180, 80, 100, 80) # Cyan
        elif val > 1.1:
            py5.fill(320, 80, 100, 60) # Pink
        else:
            py5.fill(280, 100, 100, 40) # Violet
            
        py5.box(float(s))
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
