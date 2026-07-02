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
    py5.hint(py5.DISABLE_DEPTH_TEST)

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    t = py5.frame_count * 0.02
    py5.rotate_y(t)
    py5.rotate_x(py5.sin(t * 0.5) * 0.5)
    
    # Two orbiting magnetic poles
    pole1_x = py5.cos(t * 2) * 400
    pole1_y = py5.sin(t * 1.5) * 200
    pole1_z = py5.sin(t * 2) * 400
    
    pole2_x = -pole1_x
    pole2_y = -pole1_y
    pole2_z = -pole1_z
    
    num_lines = 150
    points_per_line = 60
    
    for i in range(num_lines):
        py5.begin_shape(py5.LINE_STRIP)
        py5.no_fill()
        
        hue = (180 + i * (120 / num_lines) + t * 20) % 360
        py5.stroke(hue, 90, 100, 40)
        py5.stroke_weight(4)
        
        # Start points arranged in a sphere around pole 1
        phi = py5.acos(1 - 2 * (i / num_lines))
        theta = py5.PI * (1 + 5**0.5) * i
        
        start_x = pole1_x + py5.sin(phi) * py5.cos(theta) * 20
        start_y = pole1_y + py5.sin(phi) * py5.sin(theta) * 20
        start_z = pole1_z + py5.cos(phi) * 20
        
        cx, cy, cz = start_x, start_y, start_z
        
        for p in range(points_per_line):
            py5.vertex(cx, cy, cz)
            
            # Vector to pole 2
            dx2 = pole2_x - cx
            dy2 = pole2_y - cy
            dz2 = pole2_z - cz
            dist2 = py5.dist(cx, cy, cz, pole2_x, pole2_y, pole2_z) + 1
            
            # Magnetic field direction (simplistic dipole approximation + noise)
            force_x = dx2 / dist2
            force_y = dy2 / dist2
            force_z = dz2 / dist2
            
            # Add turbulence
            nx = py5.os_noise(cx * 0.005, cy * 0.005, cz * 0.005, t) - 0.5
            ny = py5.os_noise(cx * 0.005 + 100, cy * 0.005, cz * 0.005, t) - 0.5
            nz = py5.os_noise(cx * 0.005 + 200, cy * 0.005, cz * 0.005, t) - 0.5
            
            step_size = 20
            cx += (force_x * 0.5 + nx * 0.5) * step_size
            cy += (force_y * 0.5 + ny * 0.5) * step_size
            cz += (force_z * 0.5 + nz * 0.5) * step_size
            
            if dist2 < 50:
                break # Reached the other pole
                
        py5.end_shape()

    # Draw the poles
    py5.push_matrix()
    py5.translate(pole1_x, pole1_y, pole1_z)
    py5.fill(180, 90, 100, 80)
    py5.no_stroke()
    py5.sphere(30)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(pole2_x, pole2_y, pole2_z)
    py5.fill(300, 90, 100, 80)
    py5.no_stroke()
    py5.sphere(30)
    py5.pop_matrix()


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
