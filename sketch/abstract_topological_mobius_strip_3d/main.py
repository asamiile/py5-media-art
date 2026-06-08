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
    py5.background(240, 100, 5) # Dark obsidian violet
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Rotate scene
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_z(py5.frame_count * 0.002)
    
    py5.blend_mode(py5.ADD)
    
    # Draw Mobius strip
    steps_u = 200
    steps_v = 40
    R = py5.height * 0.4
    
    t = py5.frame_count * 0.05
    
    py5.begin_shape(py5.QUADS)
    for i in range(steps_u):
        u1 = py5.TWO_PI * i / steps_u
        u2 = py5.TWO_PI * (i + 1) / steps_u
        for j in range(steps_v):
            v1 = py5.remap(j, 0, steps_v, -R*0.3, R*0.3)
            v2 = py5.remap(j + 1, 0, steps_v, -R*0.3, R*0.3)
            
            # Parametric Mobius equations
            def mobius(u, v):
                x = (R + v * math.cos(u / 2)) * math.cos(u)
                y = (R + v * math.cos(u / 2)) * math.sin(u)
                z = v * math.sin(u / 2)
                return x, y, z
            
            x1, y1, z1 = mobius(u1, v1)
            x2, y2, z2 = mobius(u2, v1)
            x3, y3, z3 = mobius(u2, v2)
            x4, y4, z4 = mobius(u1, v2)
            
            # Flowing energy lines effect
            flow_val = (math.sin(10 * u1 - t) + math.cos(5 * v1 + t)) * 0.5 + 0.5
            
            hue = (280 + flow_val * 60 + py5.frame_count * 0.5) % 360
            alpha = py5.remap(flow_val, 0, 1, 20, 200)
            
            py5.fill(hue, 80, 100, alpha)
            py5.vertex(x1, y1, z1)
            py5.vertex(x2, y2, z2)
            py5.vertex(x3, y3, z3)
            py5.vertex(x4, y4, z4)
            
    py5.end_shape()
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
