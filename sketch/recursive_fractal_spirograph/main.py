from pathlib import Path
import shutil
import subprocess
import sys
import collections
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Trail memory
trail = collections.deque(maxlen=1500)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Global camera rotation
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.2)
    py5.rotate_z(t * 0.1)
    
    # Calculate the tip of the recursive linkages
    x, y, z = 0.0, 0.0, 0.0
    
    # Linkage parameters: (radius, speed_x, speed_y, speed_z)
    linkages = [
        (300, 1.0, 0.0, 0.5),
        (150, -2.5, 1.5, 0.0),
        (75, 4.0, -3.0, 2.0),
        (35, -8.0, 6.0, -4.0)
    ]
    
    for r, sx, sy, sz in linkages:
        x += py5.cos(t * sx) * r
        y += py5.sin(t * sy) * r
        z += py5.cos(t * sz) * py5.sin(t * sx) * r
        
    trail.append((x, y, z))
    
    # Draw the spirograph trail using a 3D ribbon (triangle strip)
    py5.no_stroke()
    
    if len(trail) > 2:
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for i, (tx, ty, tz) in enumerate(trail):
            # Calculate normal vector for ribbon width
            if i < len(trail) - 1:
                nx, ny, nz = trail[i+1]
                dx, dy, dz = nx - tx, ny - ty, nz - tz
            else:
                dx, dy, dz = tx - trail[i-1][0], ty - trail[i-1][1], tz - trail[i-1][2]
                
            # Cross product with a rough "up" vector to get width direction
            mag = py5.sqrt(dx*dx + dy*dy + dz*dz) + 0.0001
            wx, wy, wz = -dy/mag, dx/mag, 0
            
            # Width tapers off at the tail
            width = py5.remap(i, 0, len(trail), 0, 15)
            
            hue = (t * 10 + i * 0.5) % 360
            alpha = py5.remap(i, 0, len(trail), 0, 100)
            
            py5.fill(hue, 90, 100, alpha)
            py5.vertex(tx + wx * width, ty + wy * width, tz + wz * width)
            py5.vertex(tx - wx * width, ty - wy * width, tz - wz * width)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
