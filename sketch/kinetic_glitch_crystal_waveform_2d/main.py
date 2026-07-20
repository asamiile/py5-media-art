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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(20, 20, 25)
    py5.color_mode(py5.RGB, 255)
    
def draw():
    py5.background(20, 20, 25)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.05
    
    # Global rotation
    py5.rotate(t * 0.1)
    
    num_sides = 6
    radius_base = 300
    
    # Draw chromatic aberration layers
    colors = [
        (255, 0, 50),   # Red
        (0, 255, 100),  # Green
        (50, 0, 255),   # Blue
        (255, 255, 255) # White core
    ]
    
    offsets = [
        (py5.os_noise(t, 0) - 0.5) * 50,
        (py5.os_noise(0, t) - 0.5) * 50,
        (py5.os_noise(t, t) - 0.5) * 50,
        0
    ]
    
    for layer in range(4):
        py5.stroke(colors[layer][0], colors[layer][1], colors[layer][2], 200)
        py5.stroke_weight(3)
        py5.no_fill()
        
        py5.push_matrix()
        # Apply glitch displacement
        py5.translate(offsets[layer], -offsets[layer])
        
        if layer == 3:
            py5.stroke_weight(5) # Thicker white core
            
        # Draw crystalline waveforms
        for s in range(num_sides):
            angle1 = py5.TWO_PI / num_sides * s
            angle2 = py5.TWO_PI / num_sides * (s + 1)
            
            # Subdivide side into points to apply waveform
            pts = 100
            py5.begin_shape()
            for p in range(pts + 1):
                lerp_factor = p / pts
                
                # Base geometric line
                bx = py5.lerp(np.cos(angle1) * radius_base, np.cos(angle2) * radius_base, lerp_factor)
                by = py5.lerp(np.sin(angle1) * radius_base, np.sin(angle2) * radius_base, lerp_factor)
                
                # Add waveform
                wave_freq = 15.0
                wave_amp = py5.remap(py5.os_noise(s, t * 0.5), 0, 1, 0, 150)
                
                # Glitch spikes
                glitch = 0
                if py5.random(1) < 0.05:
                    glitch = (py5.random(1) - 0.5) * 200
                
                wave = np.sin(lerp_factor * py5.TWO_PI * wave_freq + t * 5) * wave_amp + glitch
                
                # Normal vector from origin
                dist = np.sqrt(bx*bx + by*by)
                nx = bx / dist
                ny = by / dist
                
                final_x = bx + nx * wave
                final_y = by + ny * wave
                
                py5.vertex(final_x, final_y)
            py5.end_shape()
            
        py5.pop_matrix()

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
