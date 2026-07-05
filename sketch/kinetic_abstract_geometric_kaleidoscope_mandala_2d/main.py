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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0, 0, 5)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_fill()
    py5.stroke_weight(2)
    py5.blend_mode(py5.ADD)

def draw():
    # Fade background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Global rotation
    py5.rotate(time_val * 0.1)
    
    # Kaleidoscope settings
    num_segments = 12
    angle_step = 2 * np.pi / num_segments
    
    # Generate some procedural shapes for this frame
    num_shapes = 8
    shapes = []
    for i in range(num_shapes):
        r = 100 + py5.noise(i * 10, time_val * 0.5) * 800
        theta = py5.noise(i * 20, time_val * 0.3) * angle_step
        size = py5.noise(i * 30, time_val * 0.8) * 150
        hue = (20 + py5.noise(i * 40, time_val * 0.1) * 60) % 360 # Gold, amber, crimson
        shapes.append((r, theta, size, hue))
    
    for i in range(num_segments):
        py5.push_matrix()
        py5.rotate(i * angle_step)
        
        # Draw the shapes in this segment
        for r, theta, size, hue in shapes:
            py5.stroke(hue, 80, 90, 80)
            
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(time_val + r * 0.01)
            
            # Draw a complex geometric element
            py5.begin_shape()
            for j in range(5):
                angle = j * 2 * np.pi / 5
                px = np.cos(angle) * size
                py5.vertex(px, np.sin(angle) * size)
            py5.end_shape(py5.CLOSE)
            
            py5.pop_matrix()
            
            # Mirror symmetry within the segment
            py5.push_matrix()
            py5.scale(1, -1)
            py5.translate(x, y)
            py5.rotate(-(time_val + r * 0.01))
            
            py5.begin_shape()
            for j in range(5):
                angle = j * 2 * np.pi / 5
                px = np.cos(angle) * size
                py5.vertex(px, np.sin(angle) * size)
            py5.end_shape(py5.CLOSE)
            
            py5.pop_matrix()
            
        py5.pop_matrix()

    # Center glowing core
    py5.no_stroke()
    core_hue = (30 + np.sin(time_val) * 20) % 360
    for r_core in range(300, 0, -20):
        py5.fill(core_hue, 90, 100, 5)
        py5.ellipse(0, 0, r_core, r_core)

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
