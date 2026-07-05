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
font = None

def setup():
    global pg, font
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 10, 15)
    
    pg = py5.create_graphics(SIZE[0], SIZE[1])
    # Create default sans-serif font
    font = py5.create_font("Helvetica-Bold", 300)
    
    FRAMES_DIR.mkdir(exist_ok=True)

words = ["SYSTEM", "FAILURE", "NULL", "VOID", "DATA", "CORRUPTION"]

def draw():
    t = py5.frame_count * 0.015
    
    # Draw new text to offscreen buffer periodically
    pg.begin_draw()
    if py5.frame_count % 90 == 1:
        pg.clear()
        pg.text_font(font)
        pg.text_align(py5.CENTER, py5.CENTER)
        
        word = words[(py5.frame_count // 90) % len(words)]
        
        # Yellow and Cyan
        if py5.frame_count % 180 < 90:
            pg.fill(255, 255, 0)
        else:
            pg.fill(0, 255, 255)
            
        pg.text(word, SIZE[0] // 2, SIZE[1] // 2)
    pg.end_draw()
    
    # Render with optical flow feedback distortion
    py5.load_pixels()
    pg.load_pixels()
    
    # To keep it fast, we do a blocky displacement in numpy
    # We'll use py5.np_pixels to manipulate the main screen buffer
    py5.load_np_pixels()
    
    H, W = SIZE[1], SIZE[0]
    
    # Create grid of coords
    y_coords, x_coords = np.mgrid[0:H, 0:W]
    
    # Calculate noise flow vectors
    nx = py5.os_noise(x_coords * 0.002, y_coords * 0.002, t) * 2 - 1
    ny = py5.os_noise(x_coords * 0.002 + 100, y_coords * 0.002 + 100, t) * 2 - 1
    
    # Distort coordinates (backward mapping)
    dist_x = np.clip(x_coords - nx * 10, 0, W - 1).astype(np.int32)
    dist_y = np.clip(y_coords - ny * 10, 0, H - 1).astype(np.int32)
    
    # Feedback the current screen, warped by flow
    warped_screen = py5.np_pixels[dist_y, dist_x]
    
    # Slightly decay the alpha/brightness to let it fade
    decay = 0.96
    warped_screen = (warped_screen * decay).astype(np.uint8)
    warped_screen[..., 0] = 255 # Keep alpha opaque
    
    # Overlay the new text buffer
    pg.load_np_pixels()
    pg_pixels = pg.np_pixels
    
    # Blend: where pg is not transparent (pg has text), use pg, else use warped
    mask = pg_pixels[..., 0] > 0 # Alpha channel > 0
    warped_screen[mask] = pg_pixels[mask]
    
    py5.np_pixels[:] = warped_screen
    py5.update_np_pixels()
    
    # Add CRT scanline effect on top
    py5.blend_mode(py5.MULTIPLY)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40)
    # Skip every other line
    # for y in range(0, H, 4):
    #    py5.rect(0, y, W, 2)
    # Actually, drawing rects is too slow for thousands of lines, do it in np_pixels if needed.
    # Let's skip it to keep 60fps stable, or do it fast in numpy before update_np_pixels
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
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
