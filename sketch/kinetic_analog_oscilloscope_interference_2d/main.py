from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 10  # Reduced to 10 for faster generation in loop
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    # Motion blur / phosphor decay effect
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)  # slight decay
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.02
    
    # Base frequencies driven by noise to simulate unstable analog signal
    freq_x = 3 + py5.os_noise(t * 0.1, 0.0) * 2
    freq_y = 2 + py5.os_noise(t * 0.1 + 100, 0.0) * 3
    phase_offset = py5.os_noise(t * 0.05 + 200, 0.0) * py5.TWO_PI
    
    py5.no_fill()
    
    # Draw multiple oscilloscope traces
    num_traces = 5
    for j in range(num_traces):
        py5.stroke(120 + j*10, 80, 100, 60) # Phosphor green with cyan hints
        py5.stroke_weight(2 + j*0.5)
        
        py5.begin_shape()
        for i in range(300):
            pt = i * py5.TWO_PI / 300
            
            # Oscilloscope jitter and drift
            jit_x = (py5.os_noise(i * 0.1, t + j) - 0.5) * 50
            jit_y = (py5.os_noise(i * 0.1, t + j + 50) - 0.5) * 50
            
            x = math.sin(freq_x * pt + phase_offset + j * 0.05) * (py5.width * 0.4) + jit_x
            y = math.sin(freq_y * pt + j * 0.05) * (py5.height * 0.4) + jit_y
            
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save gigabytes of local storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
