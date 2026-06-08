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
DURATION_SEC = 12
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
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.PI / 6 + math.sin(py5.frame_count * 0.003) * 0.2)
    py5.rotate_z(py5.frame_count * 0.002)
    
    py5.blend_mode(py5.ADD)
    
    box_size = 600
    steps = 40
    step_size = box_size / steps
    
    # Render stacked planes for a volumetric effect
    for z_idx in range(steps):
        z = -box_size / 2 + z_idx * step_size
        
        py5.push_matrix()
        py5.translate(0, 0, z)
        
        py5.begin_shape(py5.QUADS)
        for x_idx in range(steps):
            for y_idx in range(steps):
                x = -box_size / 2 + x_idx * step_size
                y = -box_size / 2 + y_idx * step_size
                
                # 3D Quantum Interference Function
                d1 = math.sqrt(x**2 + y**2 + z**2)
                d2 = math.sqrt((x - 150)**2 + (y + 150)**2 + (z - 100)**2)
                d3 = math.sqrt((x + 100)**2 + (y - 200)**2 + (z + 150)**2)
                
                val = (math.sin(d1 * 0.02 - t) + 
                       math.sin(d2 * 0.03 - t * 1.5) + 
                       math.cos(d3 * 0.025 + t * 0.8)) / 3.0
                
                if val > 0.3:
                    hue = (180 + val * 60 + py5.frame_count * 0.5) % 360
                    alpha = py5.remap(val, 0.3, 1.0, 0, 150)
                    
                    py5.fill(hue, 90, 100, alpha)
                    
                    s = step_size * 0.9 # Small gap between voxels/quads
                    
                    py5.vertex(x, y, 0)
                    py5.vertex(x + s, y, 0)
                    py5.vertex(x + s, y + s, 0)
                    py5.vertex(x, y + s, 0)
                    
        py5.end_shape()
        py5.pop_matrix()
        
    # Draw wireframe boundary
    py5.no_fill()
    py5.stroke(200, 50, 100, 50)
    py5.stroke_weight(2)
    py5.box(box_size)
    py5.no_stroke()
        
    py5.blend_mode(py5.BLEND)

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
