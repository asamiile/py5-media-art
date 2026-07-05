from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

pg = None

def setup():
    global pg
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 10, 12)
    pg = py5.create_graphics(SIZE[0], SIZE[1])
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    t = py5.frame_count * 0.02
    
    # Render new dynamic shapes to offscreen buffer
    pg.begin_draw()
    pg.clear()
    pg.translate(SIZE[0]/2, SIZE[1]/2)
    pg.rotate(t * 0.5)
    
    # Pulsing shape
    size = 200 + np.sin(t * 2) * 100
    
    # Colors
    c_phase = t * 0.3
    r = int((np.sin(c_phase) * 0.5 + 0.5) * 255)
    g = int((np.sin(c_phase + 2.0) * 0.5 + 0.5) * 255)
    b = int((np.sin(c_phase + 4.0) * 0.5 + 0.5) * 255)
    
    pg.no_stroke()
    pg.fill(r, g, b)
    
    pg.rect_mode(py5.CENTER)
    pg.rect(0, 0, size, size)
    
    pg.rotate(-t * 1.2)
    pg.fill(255 - r, 255 - g, 255 - b)
    pg.rect(0, 0, size * 0.5, size * 0.5)
    pg.end_draw()
    
    # Feedback processing: sample current screen, offset slightly
    py5.load_np_pixels()
    
    # Create feedback array by slightly scaling the image up and out from center
    # For speed, we will do a fast numpy slice
    
    H, W = SIZE[1], SIZE[0]
    
    # We want a tunnel effect: the center scales outward
    # To do this fast without cv2.warpAffine, we use numpy grid
    y_coords, x_coords = np.mgrid[0:H, 0:W]
    
    # Vector from center
    cx, cy = W/2, H/2
    dx = x_coords - cx
    dy = y_coords - cy
    
    # Slit-scan / tunnel math
    # Scale inwards to sample slightly smaller area (which will make the image grow outward)
    scale = 0.98 + np.sin(t) * 0.01
    rot = np.sin(t * 0.5) * 0.05
    
    # Apply rotation and scale
    dist_x = cx + dx * scale * np.cos(rot) - dy * scale * np.sin(rot)
    dist_y = cy + dx * scale * np.sin(rot) + dy * scale * np.cos(rot)
    
    # Glitch displacement: horizontal bands
    band_height = 40
    band_offset = np.sin(y_coords / band_height + t * 5) * 10
    dist_x += band_offset
    
    # Clip coordinates
    dist_x = np.clip(dist_x, 0, W - 1).astype(np.int32)
    dist_y = np.clip(dist_y, 0, H - 1).astype(np.int32)
    
    feedback_pixels = py5.np_pixels[dist_y, dist_x]
    
    # Color decay
    feedback_pixels = (feedback_pixels * 0.98).astype(np.uint8)
    feedback_pixels[..., 0] = 255 # Keep alpha
    
    # Blend the new shape buffer onto the feedback buffer
    pg.load_np_pixels()
    pg_pixels = pg.np_pixels
    
    mask = pg_pixels[..., 0] > 0
    feedback_pixels[mask] = pg_pixels[mask]
    
    # Apply slit scan vertical wipe
    # Only update the screen with feedback_pixels, but maybe mask it?
    # No, the whole screen gets the feedback.
    py5.np_pixels[:] = feedback_pixels
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
