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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 10)

def draw_spirograph(R, r, d, steps, rotation_offset):
    # Vectorized hypotrochoid calculation
    # Using a very large angle range to trace the full complex star shape
    theta = np.linspace(0, 40 * np.pi, steps)
    
    # To prevent division by zero in the ratio
    if r == 0: r = 0.001
    
    ratio = (R - r) / r
    
    # Apply global rotation offset
    theta_rot = theta + rotation_offset
    
    x = (R - r) * np.cos(theta_rot) + d * np.cos(ratio * theta)
    y = (R - r) * np.sin(theta_rot) - d * np.sin(ratio * theta)
    
    # Use py5's fast vectorized vertices
    coords = np.column_stack((x, y))
    py5.begin_shape()
    py5.vertices(coords)
    py5.end_shape()

def draw():
    # Smooth fading background to create glowing motion blur trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    t = py5.frame_count * 0.015
    
    # We will draw several nested and overlapping spirographs
    NUM_LAYERS = 12
    STEPS = 8000 # High resolution for smooth curves
    
    for i in range(NUM_LAYERS):
        # Parameters morph organically over time using sine waves
        layer_scale = 1.0 - (i * 0.07)
        
        # Base R defines the overall boundary
        R = 600 * layer_scale * (1.0 + 0.2 * np.sin(t * 0.5 + i))
        
        # r defines the rolling gear, we animate it to make the mandala "bloom"
        r = 150 * (1.0 + 0.5 * np.cos(t * 0.3 + i * 0.2))
        
        # d is the pen distance from the rolling gear center
        d = 300 * layer_scale * (1.0 + 0.3 * np.sin(t * 0.8 - i * 0.1))
        
        # Color palette: Neon Pink, Electric Blue, Glowing Orange
        red = 150 + 105 * np.sin(t + i * 0.3)
        green = 50 + 100 * np.cos(t * 0.5 - i * 0.2)
        blue = 200 + 55 * np.sin(t * 0.7 + i * 0.5)
        
        # Make outer layers fainter, inner layers brighter
        alpha = 80 + (i / NUM_LAYERS) * 100
        
        py5.stroke(abs(red), abs(green), abs(blue), alpha)
        py5.stroke_weight(2.0 - (i * 0.1))
        
        rot_offset = t * (0.2 + i * 0.05)
        draw_spirograph(R, r, d, STEPS, rot_offset)
        
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
