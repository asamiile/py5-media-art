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
    
def draw_slice(t, loop_t, radius_max, symmetry):
    # Angle for a single mirrored slice (half of the symmetry angle)
    slice_angle = py5.PI / symmetry
    
    num_elements = 30
    for i in range(num_elements):
        r_base = (i / num_elements) * radius_max
        # Oscillate radius
        r_offset = math.sin(loop_t * 2 + i * 0.4) * (radius_max * 0.1)
        r = r_base + r_offset
        
        if r < 0:
            continue
            
        hue = (340 + i * 4 + math.sin(loop_t) * 15) % 360
        py5.stroke(hue, 90, 95, 180)
        py5.stroke_weight(2 + math.sin(loop_t * 3 + i) * 1.5)
        py5.no_fill()
        
        # Bezier curve acting as a petal or intricate mandala etching
        # Start from the x-axis
        startx = r
        starty = 0
        
        # End at the edge of the slice
        endx = r * math.cos(slice_angle)
        endy = r * math.sin(slice_angle)
        
        # Control points breathing in and out
        cp1x = r * (0.5 + math.cos(loop_t + i * 0.2) * 0.3)
        cp1y = r * (0.5 + math.sin(loop_t - i * 0.2) * 0.3) * math.sin(slice_angle)
        
        cp2x = r * (0.8 + math.sin(loop_t * 2 + i * 0.3) * 0.2)
        cp2y = r * 0.2 * math.cos(loop_t + i * 0.1)
        
        py5.bezier(startx, starty, cp1x, cp1y, cp2x, cp2y, endx, endy)
        
        # Add glowing nodes at the intersection points
        if i % 3 == 0:
            py5.no_stroke()
            py5.fill(hue, 60, 100, 255)
            py5.circle(endx, endy, 6 + math.sin(loop_t * 4 + i) * 3)
            
        # Add another secondary crossing curve for complexity
        py5.stroke( (hue + 180) % 360, 80, 80, 100)
        py5.stroke_weight(1)
        py5.no_fill()
        py5.bezier(startx * 0.8, starty, 
                   cp2x, cp1y, 
                   cp1x, cp2y, 
                   endx * 1.2, endy * 1.2)

def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    
    # Deep royal blue
    py5.background(240, 90, 10)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    # Slowly rotate the entire mandala
    py5.rotate(loop_t * 0.2)
    
    symmetry = 14
    angle = py5.TWO_PI / symmetry
    radius_max = SIZE[1] * 0.45
    
    for i in range(symmetry):
        py5.push_matrix()
        py5.rotate(i * angle)
        
        # Draw forward slice
        draw_slice(t, loop_t, radius_max, symmetry)
        
        # Draw mirrored slice
        py5.scale(1, -1)
        draw_slice(t, loop_t, radius_max, symmetry)
        
        py5.pop_matrix()

    py5.color_mode(py5.RGB, 255)

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
