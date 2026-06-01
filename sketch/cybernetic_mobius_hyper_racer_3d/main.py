from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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
    
    global U_RES, V_RES, R, w
    U_RES = 200
    V_RES = 10
    R = 800
    w = 300

def draw():
    py5.background(0)
    py5.lights()
    py5.translate(SIZE[0]/2, SIZE[1]/2, -1000)
    
    t = py5.frame_count * 0.05
    
    # Camera rotation
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.2)
    
    py5.no_fill()
    py5.stroke_weight(3)
    py5.blend_mode(py5.ADD)
    
    # Draw Mobius strip
    for i in range(U_RES):
        u1 = (i / U_RES) * 4 * py5.PI
        u2 = ((i + 1) / U_RES) * 4 * py5.PI
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(V_RES + 1):
            v = py5.remap(j, 0, V_RES, -w, w)
            
            # Point 1 (u1, v)
            x1 = (R + v * np.cos(u1/2)) * np.cos(u1)
            y1 = (R + v * np.cos(u1/2)) * np.sin(u1)
            z1 = v * np.sin(u1/2)
            
            # Point 2 (u2, v)
            x2 = (R + v * np.cos(u2/2)) * np.cos(u2)
            y2 = (R + v * np.cos(u2/2)) * np.sin(u2)
            z2 = v * np.sin(u2/2)
            
            # Color logic based on u and v (animated to flow rapidly)
            flow = (u1 * 5 + v * 0.1 - t * 15) % (2 * py5.PI)
            intensity = py5.remap(np.sin(flow), -1, 1, 0, 100)
            
            if j % 2 == 0:
                py5.stroke(320, 100, intensity, 90) # Magenta
            else:
                py5.stroke(180, 100, intensity, 90) # Cyan
                
            py5.vertex(x1, y1, z1)
            py5.vertex(x2, y2, z2)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
