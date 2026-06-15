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

# Slices for the kaleidoscope
SYMMETRY = 12
SLICE_ANGLE = (2 * np.pi) / SYMMETRY

def draw_mandala_wedge(radius_scale, t):
    # This wedge fits within SLICE_ANGLE
    # We will draw a few complex layered shapes
    
    # Layer 1: Base petal
    py5.fill(150, 0, 50, 200) # Crimson
    py5.stroke(255, 200, 0, 150) # Gold
    py5.stroke_weight(3)
    py5.begin_shape()
    py5.vertex(0, 0)
    py5.vertex(100 * radius_scale, 20 * radius_scale)
    py5.vertex(250 * radius_scale, 0)
    py5.vertex(100 * radius_scale, -20 * radius_scale)
    py5.end_shape(py5.CLOSE)
    
    # Layer 2: Violet arches
    py5.no_fill()
    py5.stroke(100, 50, 255, 200) # Violet
    py5.stroke_weight(5)
    py5.arc(0, 0, 300 * radius_scale, 300 * radius_scale, -SLICE_ANGLE/2, SLICE_ANGLE/2)
    py5.arc(0, 0, 450 * radius_scale, 450 * radius_scale, -SLICE_ANGLE/4, SLICE_ANGLE/4)
    
    # Layer 3: Gold geometric accents
    pulse = 1.0 + 0.2 * np.sin(t * 3.0)
    py5.fill(255, 200, 0, 200)
    py5.no_stroke()
    py5.ellipse(180 * radius_scale, 0, 20 * radius_scale * pulse, 20 * radius_scale * pulse)
    
    # Layer 4: Deep Indigo geometric triangles
    py5.fill(30, 0, 60, 250)
    py5.stroke(255, 200, 0, 200)
    py5.stroke_weight(2)
    py5.triangle(350 * radius_scale, 0, 400 * radius_scale, 30 * radius_scale, 400 * radius_scale, -30 * radius_scale)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 0, 30) # Deep Indigo
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.02
    
    # Overall rotation
    py5.rotate(t * 0.5)
    
    # Infinite zoom trick
    # We draw the same mandala at exponentially increasing scales
    # The scale wraps around so new ones appear from the center
    # Modulo operation keeps the scale continuously growing but looping
    
    num_layers = 10
    zoom_speed = 0.05
    
    for i in range(num_layers):
        # Calculate continuous exponential scale
        layer_time = (t * zoom_speed + i * (1.0 / num_layers)) % 1.0
        
        # Exponential scaling so it appears linear in zoom
        # Scale goes from very small (e.g. 0.01) to very large (e.g. 10.0)
        scale_factor = np.exp(layer_time * 6.0) * 0.02
        
        # Fade out at the edges (when layer_time is near 1.0) 
        # and fade in at the center (when layer_time is near 0.0)
        alpha_mult = np.sin(layer_time * np.pi)
        
        py5.push_matrix()
        # Scale the whole matrix for this layer
        py5.scale(scale_factor)
        
        # We handle alpha in the drawing wedge by rotating, 
        # but to globally fade, it's easier to use blend mode or just accept the geometry overlapping
        # We will twist each layer slightly for depth
        py5.rotate(layer_time * np.pi / 4.0)
        
        # Draw the 12 wedges
        for j in range(SYMMETRY):
            py5.push_matrix()
            py5.rotate((2 * np.pi / SYMMETRY) * j)
            draw_mandala_wedge(1.0, t)
            py5.pop_matrix()
            
        py5.pop_matrix()

    # Vignette effect to darken edges
    py5.no_fill()
    for i in range(10):
        py5.stroke(0, 0, 0, i * 20)
        py5.stroke_weight(50)
        py5.ellipse(0, 0, py5.width + i * 50, py5.width + i * 50)

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
