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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 1500
particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    
    for _ in range(num_particles):
        lon = py5.random(py5.TWO_PI)
        lat = py5.random(-py5.HALF_PI, py5.HALF_PI)
        
        if py5.random(1) < 0.5:
            sl = py5.random(0.01, 0.05) * (1 if py5.random(1)<0.5 else -1)
            sa = 0
        else:
            sa = py5.random(0.01, 0.05) * (1 if py5.random(1)<0.5 else -1)
            sl = 0
            
        c = 210 if py5.random(1) < 0.6 else (320 if py5.random(1) < 0.8 else 0)
        particles.append([lon, lat, sl, sa, c])

def draw():
    # Only clear partially for a bit of structure, or don't clear at all for accumulation
    # No background clear, we just draw trails
    
    # Static camera so the lines accumulate correctly into a sphere
    py5.camera(0, 0, 900, 0, 0, 0, 0, 1, 0)
    
    # We rotate the whole sphere slowly, but wait, rotating the matrix means the lines won't connect in 2D space?
    # If we rotate the matrix, we are just drawing lines in the new rotated space, which is fine since the camera sees the 3D lines.
    # BUT if we don't clear the background, rotating the matrix will draw NEW lines over the OLD lines from a different angle, creating a smear!
    # To keep the lines crisp, we should NOT rotate the matrix if we don't clear the background, OR we clear the background with a low alpha to create a fade.
    # Let's clear with a very low alpha black.
    
    # Workaround for P3D fading: draw a full screen quad
    py5.push_matrix()
    py5.reset_matrix()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 5)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    py5.pop_matrix()
    
    # Now rotate the actual model
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.002)
    
    radius = 350
    py5.stroke_weight(2)
    
    for p in particles:
        lon, lat, sl, sa, c = p
        
        x1 = radius * py5.cos(lat) * py5.cos(lon)
        y1 = radius * py5.sin(lat)
        z1 = radius * py5.cos(lat) * py5.sin(lon)
        
        lon += sl
        lat += sa
        
        if py5.random(1) < 0.05:
            if sl != 0:
                sa = sl
                sl = 0
            else:
                sl = sa
                sa = 0
                
        if lat > py5.HALF_PI:
            lat = py5.HALF_PI
            sa *= -1
        elif lat < -py5.HALF_PI:
            lat = -py5.HALF_PI
            sa *= -1
            
        p[0] = lon
        p[1] = lat
        p[2] = sl
        p[3] = sa
        
        x2 = radius * py5.cos(lat) * py5.cos(lon)
        y2 = radius * py5.sin(lat)
        z2 = radius * py5.cos(lat) * py5.sin(lon)
        
        opacity = 30 + 30 * py5.sin(py5.frame_count * 0.1 + c)
        py5.stroke(c, 80, 100, opacity)
        py5.line(x1, y1, z1, x2, y2, z2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe
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
