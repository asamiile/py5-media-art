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
    
def draw():
    py5.background(255)
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Render two overlapping layers with difference blend mode
    py5.blend_mode(py5.DIFFERENCE)
    
    # ----- LAYER 1: Base Grid & Concentric Circles -----
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    
    # A slight slow rotation for layer 1
    py5.rotate(math.sin(t * math.pi * 2) * 0.1)
    
    py5.stroke(255, 0, 127) # Magenta-ish, difference with white makes it cyan-green
    
    num_rings = 150
    ring_spacing = 20
    for i in range(1, num_rings):
        r = i * ring_spacing
        py5.circle(0, 0, r * 2)
        
    num_spokes = 300
    for i in range(num_spokes):
        angle = (i / num_spokes) * py5.TWO_PI
        x = math.cos(angle) * (num_rings * ring_spacing)
        y = math.sin(angle) * (num_rings * ring_spacing)
        py5.line(0, 0, x, y)
        
    py5.pop_matrix()
    
    # ----- LAYER 2: Moving Grid & Concentric Circles -----
    py5.push_matrix()
    
    # Move the center in a Lissajous curve
    cx = py5.width / 2 + math.sin(t * math.pi * 2) * 300
    cy = py5.height / 2 + math.cos(t * math.pi * 4) * 150
    
    py5.translate(cx, cy)
    
    # Faster rotation
    py5.rotate(-t * math.pi * 2)
    
    py5.stroke(0, 255, 255) # Cyan, difference makes it red
    
    # Create the interference pattern
    for i in range(1, num_rings):
        r = i * ring_spacing
        py5.circle(0, 0, r * 2)
        
    for i in range(num_spokes):
        angle = (i / num_spokes) * py5.TWO_PI
        x = math.cos(angle) * (num_rings * ring_spacing)
        y = math.sin(angle) * (num_rings * ring_spacing)
        py5.line(0, 0, x, y)
        
    py5.pop_matrix()
    
    # The combination of DIFFERENCE blending and the overlapping
    # magenta/cyan lines will create dark moire bands and vivid colored fringes.
    
    py5.blend_mode(py5.BLEND) # Reset blend mode
    
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
